import asyncio

from fastapi import APIRouter
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
            top_users = await redis_client.zrange("global_xp", 0, -1, withscores=True)
            if not top_users:
                continue

            async with AsyncSessionLocal() as db:
                async with db.begin():
                    for item in top_users:
                        user_id = int(item[0].decode('utf-8') if isinstance(item[0], bytes) else item[0])
                        xp = float(item[1])
                        level = get_level_from_xp(xp)

                        stats = await redis_client.hgetall(f"user_stats:{user_id}")
                        msg_count = int(stats.get(b"messages", stats.get("messages", 0)))
                        voice_mins = int(stats.get(b"voice_mins", stats.get("voice_mins", 0)))

                        result = await db.execute(select(MemberStats).where(MemberStats.user_id == user_id))
                        db_stat = result.scalars().first()

                        if db_stat:
                            db_stat.xp = xp
                            db_stat.level = level
                            db_stat.messages_count = msg_count
                            db_stat.voice_minutes = voice_mins
                        else:
                            new_stat = MemberStats(
                                user_id=user_id, xp=xp, level=level, 
                                messages_count=msg_count, voice_minutes=voice_mins
                            )
                            db.add(new_stat)
            logger.info("[LEVELS] Автоматический бэкап опыта из Redis в PostgreSQL выполнен.")
        except Exception as e:
            logger.error(f"[LEVELS] Ошибка фоновой синхронизации: {e}")

@router.get("/leaderboard")
async def get_web_leaderboard():
    top_users = await redis_client.zrevrange("global_xp", 0, 49, withscores=True)
    leaderboard = []
    for rank_index, item in enumerate(top_users, start=1):
        user_id = item[0].decode('utf-8') if isinstance(item[0], bytes) else item[0]
        xp = float(item[1])
        leaderboard.append({
            "rank": rank_index, "user_id": user_id, 
            "level": get_level_from_xp(xp), "xp": int(xp)
        })
    return {"status": "ok", "data": leaderboard}

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