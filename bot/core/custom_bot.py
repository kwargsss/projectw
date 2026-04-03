import disnake
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
            self.logger.info("[SYSTEM] Успешное подключение к Redis!")
        except Exception as e:
            self.logger.error(f"[ERROR] REDIS НЕ ОТВЕЧАЕТ: {e}")
        
        await super().start(*args, **kwargs)

    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CheckFailure):
            try:
                await ctx.message.delete()
            except:
                pass
            await ctx.send(f"❌ {error}", delete_after=5.0)
            return
        
        if isinstance(error, commands.CommandNotFound):
            return

        self.logger.error(f"[ERROR] Ошибка в команде {ctx.command}: {error}")

    async def on_slash_command_error(self, inter: disnake.ApplicationCommandInteraction, error: commands.CommandError):
        if isinstance(error, commands.CheckFailure):
            if not inter.response.is_done():
                await inter.response.send_message(f"❌ {error}", ephemeral=True)
            else:
                await inter.followup.send(f"❌ {error}", ephemeral=True)
            return

        self.logger.error(f"[ERROR] Ошибка в slash-команде {inter.application_command.name}: {error}")