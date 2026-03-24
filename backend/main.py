import os
import uvicorn
import aiohttp
import jwt

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timedelta
from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from database import get_db, init_db, User, redis_client
from tg_logger import setup_logger


load_dotenv()

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Discord Bot Dashboard API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

logger = setup_logger("backend", os.getenv("TG_BOT_TOKEN"), os.getenv("TG_CHAT_ID"))

# [ПРОДАКШЕН]: Удали localhost и оставь только свой домен "https://domain.ru"
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI") 
JWT_SECRET = os.getenv("JWT_SECRET", "super_secret_local_key_123")
TOKEN_URL = "https://discord.com/api/oauth2/token"
API_BASE_URL = "https://discord.com/api/v10"

@app.on_event("startup")
async def startup_event():
    await init_db()
    logger.info("Бэкенд запущен, БД проверена")

@app.get("/api/auth/login")
@limiter.limit("5/minute")
async def auth_login(request: Request):
    scopes = "identify guilds"
    auth_url = (
        f"https://discord.com/oauth2/authorize?client_id={CLIENT_ID}&"
        f"redirect_uri={REDIRECT_URI}&response_type=code&scope={scopes}"
    )
    return {"url": auth_url}

@app.get("/api/auth/callback")
@limiter.limit("5/minute")
async def auth_callback(request: Request, code: str, db: AsyncSession = Depends(get_db)):
    if not code:
        raise HTTPException(status_code=400, detail="Code not provided")

    async with aiohttp.ClientSession() as session:
        data = {
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': REDIRECT_URI,
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        async with session.post(TOKEN_URL, data=data, headers=headers) as response:
            token_data = await response.json()
            if 'error' in token_data:
                # [ПРОДАКШЕН]: Замени http://localhost:5173 на https://domain.ru
                return RedirectResponse(url="http://localhost:5173/login?error=oauth_failed")
            
            access_token = token_data['access_token']

        headers = {'Authorization': f'Bearer {access_token}'}
        async with session.get(f"{API_BASE_URL}/users/@me", headers=headers) as response:
            user_info = await response.json()

        discord_id = int(user_info['id'])
        async with db.begin():
            result = await db.execute(select(User).where(User.id == discord_id))
            db_user = result.scalars().first()
            
            if db_user:
                db_user.username = user_info['username']
                db_user.last_login = datetime.utcnow()
            else:
                db_user = User(
                    id=discord_id,
                    username=user_info['username'],
                    discriminator=user_info['discriminator'],
                    avatar_hash=user_info.get('avatar')
                )
                db.add(db_user)

    token_payload = {
        "sub": str(db_user.id),
        "username": db_user.username,
        "exp": datetime.utcnow() + timedelta(days=7) 
    }
    token = jwt.encode(token_payload, JWT_SECRET, algorithm="HS256")

    # [ПРОДАКШЕН]: Замени http://localhost:5173 на https://domain.ru
    response = RedirectResponse(url="http://localhost:5173/dashboard")

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False,         # [ПРОДАКШЕН]: Поставь True, когда будет работать HTTPS
        samesite="lax",
        max_age=7 * 24 * 3600
        # domain=".domain.ru" # [ПРОДАКШЕН]: Раскоментируй эту строку и впиши свой домен
    )
    return response

@app.get("/api/auth/me")
async def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Не авторизован")
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return {"id": payload["sub"], "username": payload["username"]}
    except:
        raise HTTPException(status_code=401, detail="Токен недействителен или просрочен")

@app.post("/api/auth/logout")
async def logout(request: Request):
    response = JSONResponse(content={"status": "ok"})
    # [ПРОДАКШЕН]: Добавь параметр domain=".domain.ru", чтобы кука удалилась правильно
    response.delete_cookie("access_token")
    return response

@app.get("/api/stats")
@limiter.limit("60/minute")
async def get_server_stats(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Сначала войдите в систему")

    stats_json = await redis_client.get("guild_stats")
    if not stats_json:
        return {"status": "error", "data": {"name": "N/A", "member_count": 0}}
    
    import json
    return {"status": "ok", "data": json.loads(stats_json)}

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)