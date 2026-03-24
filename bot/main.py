import os
import disnake
import json
import redis.asyncio as redis

from disnake.ext import commands, tasks
from dotenv import load_dotenv
from tg_logger import setup_logger


load_dotenv()

logger = setup_logger("bot", os.getenv("TG_BOT_TOKEN"), os.getenv("TG_CHAT_ID"))

redis_client = redis.from_url(
    os.getenv("REDIS_URL"),
    decode_responses=True,
    health_check_interval=30
)

bot = commands.InteractionBot()

@tasks.loop(minutes=5)
async def update_stats_cache():
    if not bot.guilds:
        return

    guild = bot.guilds[0]
    
    stats = {
        "name": guild.name,
        "member_count": guild.member_count,
        "online": sum(1 for m in guild.members if m.status != disnake.Status.offline)
    }

    await redis_client.set("guild_stats", json.dumps(stats), ex=360)
    logger.info(f"Статистика сервера '{guild.name}' обновлена в Redis кэше.")

@bot.event
async def on_ready():
    logger.info(f"Бот успешно запущен как {bot.user}")
    update_stats_cache.start()

@bot.slash_command(description="Проверить статус бота")
async def ping(inter: disnake.ApplicationCommandInteraction):
    logger.info(f"Команда /ping использована пользователем {inter.author} (ID: {inter.author.id})")

if __name__ == "__main__":
    bot.run(os.getenv("BOT_TOKEN"))