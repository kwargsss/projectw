import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DATABASE_URL = os.getenv("DATABASE_URL", "").replace("?sslmode=require", "")
    REDIS_URL = os.getenv("REDIS_URL")

    DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
    DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
    DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI")
    DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
    ADMIN_DISCORD_ID = int(os.getenv("ADMIN_DISCORD_ID", 0))

    TOKEN_URL = "https://discord.com/api/oauth2/token"
    API_BASE_URL = "https://discord.com/api/v10"

    JWT_SECRET = os.getenv("JWT_SECRET")

    FRONTEND_URL = os.getenv("FRONTEND_URL")
    APP_DOMAIN = os.getenv("APP_DOMAIN", "http://localhost:8000")
    
    ALLOWED_ORIGINS = [
        FRONTEND_URL,
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # Telegram Logger
    TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
    TG_CHAT_ID = os.getenv("TG_CHAT_ID")