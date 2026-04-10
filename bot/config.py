import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
    TG_CHAT_ID = os.getenv("TG_CHAT_ID")
    REDIS_URL = os.getenv("REDIS_URL")

    ADMIN_ROLE_ID = int(os.getenv("ADMIN_ROLE_ID", 0))
    SUPPORT_ROLE_ID = int(os.getenv("SUPPORT_ROLE_ID", 0))
    TICKET_CATEGORY_SERVER = int(os.getenv("TICKET_CATEGORY_SERVER", 0))
    TICKET_CATEGORY_TECH = int(os.getenv("TICKET_CATEGORY_TECH", 0))
    ARCHIVE_CHANNEL_ID = int(os.getenv("ARCHIVE_CHANNEL_ID", 0))

    LAVALINK_HOST = os.getenv("LAVALINK_HOST")
    LAVALINK_PORT = int(os.getenv("LAVALINK_PORT"))
    LAVALINK_PASSWORD = os.getenv("LAVALINK_PASSWORD")

    YANDEX_TOKEN = os.getenv("YANDEX_TOKEN")

    _raw_tokens = os.getenv("WORKER_TOKENS", "")
    WORKER_TOKENS = [t.strip() for t in _raw_tokens.split(",") if t.strip()]