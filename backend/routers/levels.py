import asyncio

from fastapi import APIRouter, Query
from sqlalchemy.future import select
from database import redis_client, AsyncSessionLocal
from models import MemberStats
from core.logger import setup_logger
from config import Config


router = APIRouter(prefix="/api/levels", tags=["Levels & Economy"])
logger = setup_logger("backend_levels", Config.TG_BOT_TOKEN, Config.TG_CHAT_ID)

def get_level_from_xp(xp: float) -> int:
    return int((xp / 100) ** 0.5)

async def background_sync_task():
    while True:
        await asyncio.sleep(900)
        try:
            u_xp = await redis_client.zrange("global_xp", 0, -1)
            u_msg = await redis_client.zrange("global_messages", 0, -1)
            u_voice = await redis_client.zrange("global_voice_mins", 0, -1)
            
            all_uids = set(u_xp) | set(u_msg) | set(u_voice)
            if not all_uids: continue

            async with AsyncSessionLocal() as db:
                async with db.begin():
                    for uid_val in all_uids:
                        uid_str = uid_val.decode() if isinstance(uid_val, bytes) else str(uid_val)
                        uid_int = int(uid_str)
                        
                        xp_score = await redis_client.zscore("global_xp", uid_str)
                        xp = float(xp_score) if xp_score else 0.0
                        
                        stats = await redis_client.hgetall(f"user_stats:{uid_str}")
                        def get_val(k):
                            v = stats.get(k) or stats.get(k.encode())
                            return int(v.decode() if isinstance(v, bytes) else (v or 0))
                        
                        msgs = get_val("messages")
                        v_mins = get_val("voice_mins")

                        result = await db.execute(select(MemberStats).where(MemberStats.user_id == uid_int))
                        db_stat = result.scalars().first()

                        if db_stat:
                            db_stat.xp = xp
                            db_stat.level = get_level_from_xp(xp)
                            db_stat.messages_count = msgs
                            db_stat.voice_minutes = v_mins
                        else:
                            db.add(MemberStats(user_id=uid_int, xp=xp, level=get_level_from_xp(xp), 
                                               messages_count=msgs, voice_minutes=v_mins))
            logger.info(f"[LEVELS] Синхронизировано {len(all_uids)} пользователей.")
        except Exception as e:
            logger.error(f"[LEVELS] Ошибка синхронизации: {e}")

@router.get("/leaderboard")
async def get_web_leaderboard(type: str = Query("xp", enum=["xp", "messages", "voice"])):
    keys = {"xp": "global_xp", "messages": "global_messages", "voice": "global_voice_mins"}
    rk = keys.get(type, "global_xp")
    
    top = await redis_client.zrevrange(rk, 0, 49, withscores=True)
    data = []
    for rank, (uid_raw, score) in enumerate(top, 1):
        uid = uid_raw.decode() if isinstance(uid_raw, bytes) else str(uid_raw)
        item = {"rank": rank, "user_id": uid, "score": int(float(score))}
        if type == "xp": item["level"] = get_level_from_xp(float(score))
        data.append(item)
        
    return {"status": "ok", "data": data}

@router.get("/user/{user_id}")
async def get_user_web_stats(user_id: int):
    xp = await redis_client.zscore("global_xp", str(user_id))
    if not xp: return {"status": "not_found"}

    xp = float(xp)
    rank_index = await redis_client.zrevrank("global_xp", str(user_id))
    stats = await redis_client.hgetall(f"user_stats:{user_id}")
    
    def dec(val):
        if not val: return 0
        return int(val.decode('utf-8') if isinstance(val, bytes) else val)
    
    return {
        "status": "ok",
        "rank": (rank_index + 1) if rank_index is not None else 0,
        "level": get_level_from_xp(xp),
        "xp": int(xp),
        "messages": dec(stats.get(b"messages", stats.get("messages"))),
        "voice_mins": dec(stats.get(b"voice_mins", stats.get("voice_mins")))
    }