import os
import disnake

from core.custom_bot import Bot
from config import Config

bot = Bot(
    command_prefix="!", 
    intents=disnake.Intents.all(),
    help_command=None
)

@bot.event
async def on_ready():
    bot.logger.info(f"[SYSTEM] Бот успешно запущен как {bot.user}")

if __name__ == "__main__":
    base_dir = os.path.dirname(__file__)
    cogs_dir = os.path.join(base_dir, "cogs")
    
    if os.path.exists(cogs_dir):
        for root, dirs, files in os.walk(cogs_dir):
            for filename in files:
                if filename.endswith(".py") and not filename.startswith("__"):
                    file_path = os.path.join(root, filename)
                    rel_path = os.path.relpath(file_path, base_dir)
                    cog_path = rel_path.replace(os.sep, ".")[:-3]
                    
                    try:
                        bot.load_extension(cog_path)
                    except Exception as e:
                        bot.logger.error(f"[ERROR] Ошибка при загрузке модуля {cog_path}: {e}")
    else:
        bot.logger.warning("[SYSTEM] Папка 'cogs' не найдена. Модули не загружены.")

    bot.run(Config.BOT_TOKEN)