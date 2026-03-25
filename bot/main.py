import os
import disnake
import json
import redis.asyncio as redis

from datetime import datetime
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

intents = disnake.Intents.default()
intents.members = True          
intents.presences = True        
intents.message_content = True  

bot = commands.InteractionBot(intents=intents)

@bot.event
async def on_message(message: disnake.Message):
    if not message.author.bot:
        await redis_client.incr("stats_messages_24h")

@bot.event
async def on_application_command(inter: disnake.ApplicationCommandInteraction):
    await redis_client.incr("stats_commands_24h")

@tasks.loop(seconds=5)
async def update_stats_cache():
    if not bot.guilds:
        return

    guild = bot.guilds[0]
    
    msg_count = await redis_client.get("stats_messages_24h")
    cmd_count = await redis_client.get("stats_commands_24h")
    online_count = sum(1 for m in guild.members if m.status != disnake.Status.offline)

    today_str = datetime.now().strftime("%d.%m")
    history_str = await redis_client.get("weekly_history")
    
    history = json.loads(history_str) if history_str else []

    if not history or history[-1]["date"] != today_str:
        await redis_client.set("stats_messages_24h", 0)
        await redis_client.set("stats_commands_24h", 0)
        msg_count = 0
        cmd_count = 0
        logger.info(f"Наступил новый день ({today_str})! Суточная статистика сброшена.")
        
        if len(history) >= 7:
            history.pop(0)
        history.append({"date": today_str, "messages": 0, "commands": 0})

    history[-1]["messages"] = int(msg_count) if msg_count else 0
    history[-1]["commands"] = int(cmd_count) if cmd_count else 0

    await redis_client.set("weekly_history", json.dumps(history))

    stats = {
        "name": guild.name,
        "member_count": guild.member_count,
        "online": online_count,
        "messages_24h": int(msg_count) if msg_count else 0,
        "commands_24h": int(cmd_count) if cmd_count else 0
    }

    await redis_client.set("guild_stats", json.dumps(stats), ex=30)

@bot.event
async def on_ready():
    logger.info(f"Бот успешно запущен как {bot.user}")
    update_stats_cache.start()

@bot.slash_command(description="Тестовая команда для проверки графика")
async def test_graph(inter: disnake.ApplicationCommandInteraction):
    await inter.response.send_message("Команда успешно засчитана в реальный график! 🚀", ephemeral=True)

if __name__ == "__main__":
    bot.run(os.getenv("BOT_TOKEN"))