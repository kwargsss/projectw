import json

from fastapi import APIRouter, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from config import Config
from database import get_db, redis_client
from models import User
from schemas import EmbedStructure, EmbedV2Structure, NotificationSettingsModel
from dependencies import verify_admin_access, verify_support_access
from core.limiter import limiter
from core.logger import setup_logger

router = APIRouter(prefix="/api", tags=["Bot Features"])
logger = setup_logger("backend", Config.TG_BOT_TOKEN, Config.TG_CHAT_ID)

@router.post("/embed/send")
@limiter.limit("30/minute") 
async def send_embed_message(request: Request, payload: EmbedStructure, db: AsyncSession = Depends(get_db)):
    admin_info = await verify_admin_access(request, db)
    bot_payload = payload.model_dump(exclude_none=True)
    avatar_url = f"https://cdn.discordapp.com/avatars/{admin_info['sub']}/{admin_info['avatar']}.png" if admin_info.get('avatar') else "https://cdn.discordapp.com/embed/avatars/0.png"
    bot_payload['footer'] = {"text": f"Отправлено администратором: {admin_info['username']}", "icon_url": avatar_url}
    
    await redis_client.publish("projectw_embed_commands", json.dumps(bot_payload))
    logger.warning(f"[ACTION] Админ {admin_info['username']} отправил Embed сообщение в канал {payload.channel_id}.")
    return {"status": "ok"}

@router.post("/embed/send_v2")
@limiter.limit("30/minute") 
async def send_embed_message_v2(request: Request, payload: EmbedV2Structure, db: AsyncSession = Depends(get_db)):
    admin_info = await verify_admin_access(request, db)
    bot_payload = payload.model_dump(exclude_none=True)
    avatar_url = f"https://cdn.discordapp.com/avatars/{admin_info['sub']}/{admin_info['avatar']}.png" if admin_info.get('avatar') else "https://cdn.discordapp.com/embed/avatars/0.png"
    bot_payload['footer'] = {"text": f"Отправлено администратором: {admin_info['username']}", "icon_url": avatar_url}
    
    await redis_client.publish("projectw_embed_v2_commands", json.dumps(bot_payload))
    logger.warning(f"[ACTION] Админ {admin_info['username']} отправил V2 Embed в канал {payload.channel_id}.")
    return {"status": "ok"}

@router.get("/settings/notifications")
@limiter.limit("60/minute")
async def get_notifications(request: Request, db: AsyncSession = Depends(get_db)):
    await verify_admin_access(request, db)
    data = await redis_client.get("notification_settings")
    if data: return {"status": "ok", "data": json.loads(data)}
    default_data = {
        "welcome": {"enabled": False, "channel_id": "", "embed_type": "v1", "color": "#5865F2", "blocks": []},
        "goodbye": {"enabled": False, "channel_id": "", "embed_type": "v1", "color": "#ED4245", "blocks": []}
    }
    return {"status": "ok", "data": default_data}

@router.post("/settings/notifications")
@limiter.limit("30/minute")
async def save_notifications(request: Request, payload: NotificationSettingsModel, db: AsyncSession = Depends(get_db)):
    admin_info = await verify_admin_access(request, db)
    await redis_client.set("notification_settings", payload.model_dump_json())
    logger.warning(f"[ACTION] Админ {admin_info['username']} обновил настройки оповещений.")
    return {"status": "ok"}

@router.get("/channels")
@limiter.limit("60/minute")
async def get_channels(request: Request, db: AsyncSession = Depends(get_db)):
    await verify_admin_access(request, db)
    data = await redis_client.get("guild_channels")
    return {"status": "ok", "data": json.loads(data) if data else []}

@router.get("/stats")
@limiter.limit("60/minute")
async def get_stats(request: Request, db: AsyncSession = Depends(get_db)): 
    await verify_support_access(request, db)
    try:
        data = await redis_client.get("guild_stats")
        if data:
            stats = json.loads(data)
            async with db.begin():
                result = await db.execute(select(User).where(User.role.in_(["admin", "superadmin", "support"])))
                stats["admin_count"] = len(result.scalars().all())
            weekly_data = await redis_client.get("weekly_history")
            stats["weekly"] = json.loads(weekly_data) if weekly_data else []
            return {"status": "ok", "data": stats}
        return {"status": "error", "message": "No data in Redis"}
    except Exception as e: return {"status": "error", "message": str(e)}

@router.get("/bot")
async def get_bot_info(request: Request): 
    return {"status": "ok", "data": request.app.state.bot_info}