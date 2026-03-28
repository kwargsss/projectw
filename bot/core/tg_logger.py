import logging
import asyncio
import aiohttp

from datetime import datetime

CATEGORIES = {
    "[SYSTEM]": {"emoji": "⚙️", "name": "#СИСТЕМА"},
    "[AUTH]": {"emoji": "🔐", "name": "#АВТОРИЗАЦИЯ"},
    "[SECURITY]": {"emoji": "🛡️", "name": "#БЕЗОПАСНОСТЬ"},
    "[ACTION]": {"emoji": "⚡", "name": "#ДЕЙСТВИЕ_КОМАНДЫ"},
    "[STATS]": {"emoji": "📊", "name": "#СТАТИСТИКА"},
    "[ERROR]": {"emoji": "❌", "name": "#ОШИБКА"},
    "[WARNING]": {"emoji": "⚠️", "name": "#ВНИМАНИЕ"},
}

class TelegramBotHandler(logging.Handler):
    def __init__(self, bot_token: str, chat_id: str):
        super().__init__()
        self.bot_token = bot_token
        self.chat_id = chat_id

    async def _send_async(self, url, payload):
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(url, json=payload, timeout=5)
        except Exception:
            pass

    def emit(self, record):
        raw_message = record.getMessage()

        if record.name not in ["backend", "bot"] and record.levelno < logging.WARNING:
            return

        category_emoji = "ℹ️"
        category_name = "#ИНФОРМАЦИЯ"
        message = raw_message

        for tag, meta in CATEGORIES.items():
            if raw_message.startswith(tag):
                category_emoji = meta["emoji"]
                category_name = meta["name"]
                message = raw_message.replace(tag, "").strip()
                break
        else:
            if record.levelno >= logging.CRITICAL:
                category_emoji, category_name = "🆘", "#КРИТИЧЕСКАЯ ОШИБКА"
            elif record.levelno >= logging.ERROR:
                category_emoji, category_name = "❌", "#ОШИБКА"
            elif record.levelno >= logging.WARNING:
                category_emoji, category_name = "⚠️", "#ПРЕДУПРЕЖДЕНИЕ"

        time_str = datetime.utcnow().strftime('%d.%m.%Y %H:%M:%S')
        service_name = "БЭКЕНД ПАНЕЛИ" if record.name == "backend" else "DISCORD БОТ"

        text = (
            f"<b>{category_emoji} {category_name}</b> | <code>{service_name}</code>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"{message}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"<i>🕒 {time_str} UTC</i>"
        )

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._send_async(url, payload))
        except RuntimeError:
            pass

def setup_logger(name, tg_token, tg_chat_id, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    if logger.hasHandlers():
        logger.handlers.clear()
        
    logger.addHandler(console_handler)
    
    if tg_token and tg_chat_id:
        tg_handler = TelegramBotHandler(tg_token, tg_chat_id)
        logger.addHandler(tg_handler)
        
    return logger