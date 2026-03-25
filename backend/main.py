import os
import uvicorn
import aiohttp
import jwt
import json

from pydantic import BaseModel
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
JWT_SECRET = os.getenv("JWT_SECRET")
ADMIN_DISCORD_ID = int(os.getenv("ADMIN_DISCORD_ID", 0))
TOKEN_URL = "https://discord.com/api/oauth2/token"
API_BASE_URL = "https://discord.com/api/v10"

BOT_INFO = {
    "id": None,
    "username": "Загрузка...",
    "avatar": None
}

class RoleUpdate(BaseModel):
    user_id: int
    role: str

@app.on_event("startup")
async def startup_event():
    await init_db()
    logger.info("Бэкенд запущен, БД проверена.")

    bot_token = os.getenv("DISCORD_BOT_TOKEN")
    if bot_token:
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bot {bot_token}"}
            async with session.get(f"{API_BASE_URL}/users/@me", headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    BOT_INFO["id"] = data["id"]
                    BOT_INFO["username"] = data["username"]
                    BOT_INFO["avatar"] = data.get("avatar")
                    logger.info(f"Данные бота успешно загружены: {BOT_INFO['username']}")
                else:
                    logger.warning("Не удалось загрузить данные бота из Discord API")

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

        current_role = "admin" if discord_id == ADMIN_DISCORD_ID else "user"

        async with db.begin():
            result = await db.execute(select(User).where(User.id == discord_id))
            db_user = result.scalars().first()
            
            if db_user:
                db_user.username = user_info['username']
                db_user.last_login = datetime.utcnow()
                if discord_id == ADMIN_DISCORD_ID:
                    db_user.role = "superadmin"
            else:
                db_user = User(
                    id=discord_id, username=user_info['username'],
                    discriminator=user_info['discriminator'], avatar_hash=user_info.get('avatar'),
                    role=current_role
                )
                db.add(db_user)

    token_payload = {
        "sub": str(db_user.id),
        "username": db_user.username,
        "avatar": db_user.avatar_hash,
        "role": db_user.role,
        "exp": datetime.utcnow() + timedelta(days=7) 
    }
    token = jwt.encode(token_payload, JWT_SECRET, algorithm="HS256")

    # [ПРОДАКШЕН]: Замени http://localhost:5173 на https://domain.ru
    response = RedirectResponse(url="http://localhost:5173/")

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
async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)): # Добавили доступ к БД
    token = request.cookies.get("access_token")
    if not token: 
        raise HTTPException(status_code=401, detail="Не авторизован")
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = int(payload["sub"])

        async with db.begin():
            result = await db.execute(select(User).where(User.id == user_id))
            db_user = result.scalars().first()
            
            if not db_user:
                raise HTTPException(status_code=401, detail="Пользователь не найден")
                
            return {
                "id": str(db_user.id), 
                "username": db_user.username, 
                "avatar": db_user.avatar_hash,
                "role": db_user.role
            }
    except: 
        raise HTTPException(status_code=401, detail="Токен недействителен")

def verify_superadmin(request: Request):
    token = request.cookies.get("access_token")
    if not token: raise HTTPException(status_code=401)
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        if payload.get("role") != "superadmin": raise HTTPException(status_code=403, detail="Нет прав")
        return payload
    except: raise HTTPException(status_code=401)

@app.get("/api/admins/list")
async def get_admins_list(request: Request, db: AsyncSession = Depends(get_db)):
    verify_superadmin(request)
    async with db.begin():
        stmt = select(User).where(User.role.in_(["admin", "superadmin"]))
        result = await db.execute(stmt)
        users = result.scalars().all()
        return {"status": "ok", "data": [{"id": str(u.id), "username": u.username, "avatar": u.avatar_hash, "role": u.role} for u in users]}

@app.get("/api/users/search")
async def search_users(request: Request, q: str = "", db: AsyncSession = Depends(get_db)):
    verify_superadmin(request)
    if not q or len(q) < 2: return {"status": "ok", "data": []}
    async with db.begin():
        if q.isdigit():
            stmt = select(User).where(User.id == int(q))
        else:
            stmt = select(User).where(User.username.ilike(f"%{q}%"))
        result = await db.execute(stmt)
        users = result.scalars().all()
        return {"status": "ok", "data": [{"id": str(u.id), "username": u.username, "avatar": u.avatar_hash, "role": u.role} for u in users]}

@app.post("/api/users/role")
async def update_user_role(request: Request, data: RoleUpdate, db: AsyncSession = Depends(get_db)):
    verify_superadmin(request)
    if data.user_id == ADMIN_DISCORD_ID:
        raise HTTPException(status_code=400, detail="Нельзя изменить роль создателя")
        
    async with db.begin():
        result = await db.execute(select(User).where(User.id == data.user_id))
        db_user = result.scalars().first()
        if not db_user: raise HTTPException(status_code=404, detail="Пользователь не найден")
        db_user.role = data.role
    return {"status": "ok"}

@app.post("/api/auth/logout")
async def logout(request: Request):
    response = JSONResponse(content={"status": "ok"})
    # [ПРОДАКШЕН]: Добавь параметр domain=".domain.ru", чтобы кука удалилась правильно
    response.delete_cookie("access_token")
    return response

@app.get("/api/stats")
@limiter.limit("60/minute")
async def get_stats(request: Request, db: AsyncSession = Depends(get_db)): 
    try:
        data = await redis_client.get("guild_stats")
        if data:
            stats = json.loads(data)
            
            async with db.begin():
                result = await db.execute(select(User).where(User.role.in_(["admin", "superadmin"])))
                admins = result.scalars().all()
                stats["admin_count"] = len(admins)

            weekly_data = await redis_client.get("weekly_history")
            stats["weekly"] = json.loads(weekly_data) if weekly_data else []
                
            return {"status": "ok", "data": stats}
        return {"status": "error", "message": "No data in Redis"}
    
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/bot")
async def get_bot_info():
    return {"status": "ok", "data": BOT_INFO}

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)