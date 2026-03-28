import redis.asyncio as redis

from disnake.ext import commands
from core.tg_logger import setup_logger
from config import Config

class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = setup_logger("bot", Config.TG_BOT_TOKEN, Config.TG_CHAT_ID)
        self.redis = redis.from_url(
            Config.REDIS_URL, decode_responses=True, health_check_interval=30, socket_connect_timeout=2
        )

    async def start(self, *args, **kwargs):
        try:
            await self.redis.ping()
            self.logger.info("[SYSTEM] Успешное подключение к Redis! 🟢")
        except Exception as e:
            self.logger.error(f"[ERROR] REDIS НЕ ОТВЕЧАЕТ: {e} 🔴")
        
        await super().start(*args, **kwargs)