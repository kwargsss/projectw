import json

from fastapi import APIRouter, Body
from sqlalchemy import select
from models import PrivateVoiceConfig
from database import AsyncSessionLocal, redis_client


router = APIRouter(prefix="/api/private-voice", tags=["Private Voice"])

@router.get("/{guild_id}")
async def get_config(guild_id: int):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(PrivateVoiceConfig).where(PrivateVoiceConfig.guild_id == guild_id))
        config = result.scalars().first()
        if not config:
            config = PrivateVoiceConfig(guild_id=guild_id)
            db.add(config)
            await db.commit()
            await db.refresh(config)
            
        setup_data = await redis_client.get(f"pv_setup:{guild_id}")
        is_deployed = bool(setup_data)
            
        return {
            "status": "ok",
            "data": {
                "is_enabled": config.is_enabled,
                "template": config.template,
                "default_limit": config.default_limit,
                "default_bitrate": config.default_bitrate,
                "is_deployed": is_deployed
            }
        }

@router.post("/{guild_id}")
async def save_config(guild_id: int, data: dict = Body(...)):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(PrivateVoiceConfig).where(PrivateVoiceConfig.guild_id == guild_id))
        config = result.scalars().first()
        if not config:
            config = PrivateVoiceConfig(guild_id=guild_id)
            db.add(config)
            
        config.is_enabled = data.get("is_enabled", config.is_enabled)
        config.template = data.get("template", config.template)
        config.default_limit = data.get("default_limit", config.default_limit)
        config.default_bitrate = data.get("default_bitrate", config.default_bitrate)
        
        await db.commit()

        settings_payload = {
            "is_enabled": config.is_enabled,
            "template": config.template,
            "default_limit": config.default_limit,
            "default_bitrate": config.default_bitrate
        }
        await redis_client.set(f"pv_settings:{guild_id}", json.dumps(settings_payload))
        
        return {"status": "ok"}

@router.post("/{guild_id}/deploy")
async def deploy_system(guild_id: int):
    payload = json.dumps({"action": "deploy_private_voice", "guild_id": guild_id})
    await redis_client.publish("system_controls", payload)
    return {"status": "ok"}

@router.post("/{guild_id}/undeploy")
async def undeploy_system(guild_id: int):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(PrivateVoiceConfig).where(PrivateVoiceConfig.guild_id == guild_id))
        config = result.scalars().first()
        if config:
            config.is_enabled = False
            await db.commit()
            
    payload = json.dumps({"action": "disable_private_voice", "guild_id": guild_id})
    await redis_client.publish("system_controls", payload)
    return {"status": "ok"}