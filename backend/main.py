import uvicorn
import aiohttp

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from config import Config
from database import init_db
from core.limiter import limiter
from core.logger import setup_logger
from routers import auth, tickets, users, bot

app = FastAPI(title="Discord Bot Dashboard API")

app.state.limiter = limiter
app.state.bot_info = { "id": None, "username": "Загрузка...", "avatar": None }
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

logger = setup_logger("backend", Config.TG_BOT_TOKEN, Config.TG_CHAT_ID)

app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(tickets.router)
app.include_router(users.router)
app.include_router(bot.router)

@app.on_event("startup")
async def startup_event():
    await init_db()
    logger.info("[SYSTEM] Бэкенд запущен, БД проверена.")

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