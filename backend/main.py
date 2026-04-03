import uvicorn
import aiohttp
import asyncio
import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from config import Config
from database import init_db
from core.limiter import limiter
from core.logger import setup_logger
from routers import auth, bot, tickets, users, levels, playlists

app = FastAPI(title="Discord Bot Dashboard API")

app.state.limiter = limiter
app.state.bot_info = { "id": None, "username": "Загрузка...", "avatar": None }
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

logger = setup_logger("backend", Config.TG_BOT_TOKEN, Config.TG_CHAT_ID)

app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "DELETE"],
    allow_headers=["*"],
)

os.makedirs("uploads/backgrounds", exist_ok=True)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(auth.router)
app.include_router(tickets.router)
app.include_router(users.router)
app.include_router(bot.router)
app.include_router(levels.router)

@app.on_event("startup")
async def startup_event():
    await init_db()
    logger.info("[SYSTEM] Бэкенд запущен, БД проверена.")

    asyncio.create_task(levels.background_sync_task())
    asyncio.create_task(playlists.playlist_sync_task())

    if Config.DISCORD_BOT_TOKEN:
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bot {Config.DISCORD_BOT_TOKEN}"}
            async with session.get(f"{Config.API_BASE_URL}/users/@me", headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    app.state.bot_info.update({"id": data["id"], "username": data["username"], "avatar": data.get("avatar")})
                    logger.info(f"[SYSTEM] Данные бота успешно загружены: {data['username']}")
                else: 
                    logger.warning("[ERROR] Не удалось загрузить данные бота из Discord API")

if __name__ == "__main__": 
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)