import logging
import requests

from datetime import datetime


class TelegramBotHandler(logging.Handler):
    def __init__(self, bot_token: str, chat_id: str):
        super().__init__()
        self.bot_token = bot_token
        self.chat_id = chat_id

    def emit(self, record):
        message = record.getMessage()
        
        if record.levelno == logging.INFO:
            important_keywords = ["успешно", "запущен", "вошел", "зарегистрирован"]
            if not any(word in message.lower() for word in important_keywords):
                return

        emoji = "ℹ️"
        if record.levelno >= logging.CRITICAL:
            emoji = "🆘"
        elif record.levelno >= logging.ERROR:
            emoji = "🚨"
        elif record.levelno >= logging.WARNING:
            emoji = "⚠️"
        elif "успешно" in message.lower() or "запущен" in message.lower():
            emoji = "✅"

        time_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        text = (
            f"<b>{emoji} {record.levelname}</b> | <code>{record.name}</code>\n\n"
            f"<b>Событие:</b> {message}\n"
            f"<i>{time_str} UTC</i>"
        )

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        
        try:
            requests.post(url, json=payload, timeout=5)
        except requests.exceptions.RequestException:
            pass

def setup_logger(name, tg_token, tg_chat_id, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    tg_handler = TelegramBotHandler(tg_token, tg_chat_id)

    if logger.hasHandlers():
        logger.handlers.clear()
        
    logger.addHandler(tg_handler)
    logger.addHandler(console_handler)
    return logger