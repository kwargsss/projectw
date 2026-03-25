import os
import uvicorn
import aiohttp
import jwt
import json

from pydantic import BaseModel
from typing import Optional, List
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

BOT_INFO = { "id": None, "username": "Загрузка...", "avatar": None }

class RoleUpdate(BaseModel):
    user_id: int
    role: str

class EmbedField(BaseModel):
    name: str
    value: str
    inline: bool = False

class EmbedStructure(BaseModel):
    channel_id: str
    content: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    color: Optional[str] = "#5865F2"
    author_name: Optional[str] = None
    author_icon: Optional[str] = None
    author_url: Optional[str] = None
    image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    fields: Optional[List[EmbedField]] = []

class EmbedBlock(BaseModel):
    type: str
    content: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    button_label: Optional[str] = None
    button_url: Optional[str] = None

class EmbedV2Structure(BaseModel):
    channel_id: str
    color: Optional[str] = "#5865F2"
    blocks: List[EmbedBlock] = []

@app.on_event("startup")
async def startup_event():
    await init_db()
    logger.info("[SYSTEM] Бэкенд запущен, БД проверена.")
    bot_token = os.getenv("DISCORD_BOT_TOKEN")
    if bot_token:
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bot {bot_token}"}
            async with session.get(f"{API_BASE_URL}/users/@me", headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    BOT_INFO.update({"id": data["id"], "username": data["username"], "avatar": data.get("avatar")})
                    logger.info(f"[SYSTEM] Данные бота успешно загружены: {BOT_INFO['username']}")
                else: logger.warning("[ERROR] Не удалось загрузить данные бота из Discord API")

def get_user_from_token(request: Request):
    token = request.cookies.get("access_token")
    if not token: raise HTTPException(status_code=401, detail="Не авторизован")
    try: return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except: raise HTTPException(status_code=401, detail="Токен недействителен")

def verify_admin_access(request: Request):
    payload = get_user_from_token(request)
    if payload.get("role") not in ["admin", "superadmin"]: raise HTTPException(status_code=403, detail="Нет прав доступа")
    return payload

def verify_superadmin_access(request: Request):
    payload = get_user_from_token(request)
    if payload.get("role") != "superadmin": raise HTTPException(status_code=403, detail="Требуются права Главного Админа")
    return payload

@app.get("/api/auth/login")
@limiter.limit("5/minute")
async def auth_login(request: Request):
    auth_url = f"https://discord.com/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=identify guilds"
    return {"url": auth_url}

@app.get("/api/auth/callback")
@limiter.limit("5/minute")
async def auth_callback(request: Request, code: str, db: AsyncSession = Depends(get_db)):
    if not code: raise HTTPException(status_code=400, detail="Code not provided")
    async with aiohttp.ClientSession() as session:
        data = { 'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET, 'grant_type': 'authorization_code', 'code': code, 'redirect_uri': REDIRECT_URI }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        async with session.post(TOKEN_URL, data=data, headers=headers) as response:
            token_data = await response.json()
            if 'error' in token_data: return RedirectResponse(url="http://localhost:5173/login?error=oauth_failed")
            access_token = token_data['access_token']

        headers = {'Authorization': f'Bearer {access_token}'}
        async with session.get(f"{API_BASE_URL}/users/@me", headers=headers) as response:
            user_info = await response.json()

        discord_id = int(user_info['id'])
        async with db.begin():
            result = await db.execute(select(User).where(User.id == discord_id))
            db_user = result.scalars().first()
            is_new = False
            if db_user:
                db_user.username = user_info['username']
                db_user.avatar_hash = user_info.get('avatar')
                db_user.last_login = datetime.utcnow()
                if discord_id == ADMIN_DISCORD_ID and db_user.role != "superadmin": db_user.role = "superadmin"
            else:
                is_new = True
                new_role = "superadmin" if discord_id == ADMIN_DISCORD_ID else "user"
                db_user = User(id=discord_id, username=user_info['username'], discriminator=user_info['discriminator'], avatar_hash=user_info.get('avatar'), role=new_role)
                db.add(db_user)
                
        if is_new: logger.info(f"[AUTH] Новый пользователь: {db_user.username} (ID: {db_user.id})")
        else: logger.info(f"[AUTH] Вход: {db_user.username} (Роль: {db_user.role})")

    token_payload = { "sub": str(db_user.id), "username": db_user.username, "avatar": db_user.avatar_hash, "role": db_user.role, "exp": datetime.utcnow() + timedelta(days=7) }
    token = jwt.encode(token_payload, JWT_SECRET, algorithm="HS256")
    response = RedirectResponse(url="http://localhost:5173/")
    response.set_cookie(key="access_token", value=token, httponly=True, secure=False, samesite="lax", max_age=7*24*3600)
    return response

@app.get("/api/auth/me")
async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)):
    payload = get_user_from_token(request)
    async with db.begin():
        result = await db.execute(select(User).where(User.id == int(payload["sub"])))
        db_user = result.scalars().first()
        if not db_user: raise HTTPException(status_code=401, detail="Пользователь не найден")
        return {"id": str(db_user.id), "username": db_user.username, "avatar": db_user.avatar_hash, "role": db_user.role}

@app.get("/api/admins/list")
async def get_admins_list(request: Request, db: AsyncSession = Depends(get_db)):
    verify_superadmin_access(request)
    async with db.begin():
        stmt = select(User).where(User.role.in_(["admin", "superadmin"]))
        result = await db.execute(stmt)
        return {"status": "ok", "data": [{"id": str(u.id), "username": u.username, "avatar": u.avatar_hash, "role": u.role} for u in result.scalars().all()]}

@app.get("/api/users/search")
async def search_users(request: Request, q: str = "", db: AsyncSession = Depends(get_db)):
    verify_superadmin_access(request)
    if not q or len(q) < 2: return {"status": "ok", "data": []}
    async with db.begin():
        stmt = select(User).where(User.id == int(q)) if q.isdigit() else select(User).where(User.username.ilike(f"%{q}%"))
        result = await db.execute(stmt)
        return {"status": "ok", "data": [{"id": str(u.id), "username": u.username, "avatar": u.avatar_hash, "role": u.role} for u in result.scalars().all()]}

@app.post("/api/users/role")
async def update_user_role(request: Request, data: RoleUpdate, db: AsyncSession = Depends(get_db)):
    admin_payload = verify_superadmin_access(request)
    if data.user_id == ADMIN_DISCORD_ID: raise HTTPException(status_code=400, detail="Нельзя изменить роль создателя")
    async with db.begin():
        result = await db.execute(select(User).where(User.id == data.user_id))
        db_user = result.scalars().first()
        if not db_user: raise HTTPException(status_code=404, detail="Пользователь не найден")
        logger.warning(f"[SECURITY] {admin_payload['username']} {'выдал админку' if data.role == 'admin' else 'снял админку у'} {db_user.username} (ID: {db_user.id}).")
        db_user.role = data.role
    return {"status": "ok"}

@app.post("/api/auth/logout")
async def logout(request: Request):
    try: logger.info(f"[AUTH] Выход: {get_user_from_token(request)['username']}.")
    except: pass
    response = JSONResponse(content={"status": "ok"})
    response.delete_cookie("access_token")
    return response

@app.post("/api/embed/send")
@limiter.limit("30/minute") 
async def send_embed_message(request: Request, payload: EmbedStructure):
    admin_info = verify_admin_access(request)
    
    bot_payload = payload.dict(exclude_none=True)

    avatar_url = f"https://cdn.discordapp.com/avatars/{admin_info['sub']}/{admin_info['avatar']}.png" if admin_info.get('avatar') else "https://cdn.discordapp.com/embed/avatars/0.png"
    bot_payload['footer'] = {
        "text": f"Отправлено администратором: {admin_info['username']}",
        "icon_url": avatar_url
    }

    await redis_client.publish("projectw_embed_commands", json.dumps(bot_payload))
    logger.warning(f"[ACTION] Админ {admin_info['username']} отправил Embed сообщение в канал {payload.channel_id}.")

    return {"status": "ok", "message": "Команда отправлена боту"}

@app.post("/api/embed/send_v2")
@limiter.limit("30/minute") 
async def send_embed_message_v2(request: Request, payload: EmbedV2Structure):
    admin_info = verify_admin_access(request)
    bot_payload = payload.dict(exclude_none=True)

    avatar_url = f"https://cdn.discordapp.com/avatars/{admin_info['sub']}/{admin_info['avatar']}.png" if admin_info.get('avatar') else "https://cdn.discordapp.com/embed/avatars/0.png"
    bot_payload['footer'] = {
        "text": f"Отправлено администратором: {admin_info['username']}",
        "icon_url": avatar_url
    }

    await redis_client.publish("projectw_embed_v2_commands", json.dumps(bot_payload))
    logger.warning(f"[ACTION] Админ {admin_info['username']} отправил V2 Embed в канал {payload.channel_id}.")

    return {"status": "ok", "message": "Команда V2 отправлена боту"}

@app.get("/api/channels")
@limiter.limit("60/minute")
async def get_channels(request: Request):
    verify_admin_access(request)
    data = await redis_client.get("guild_channels")
    return {"status": "ok", "data": json.loads(data) if data else []}

@app.get("/api/stats")
@limiter.limit("60/minute")
async def get_stats(request: Request, db: AsyncSession = Depends(get_db)): 
    try:
        data = await redis_client.get("guild_stats")
        if data:
            stats = json.loads(data)
            async with db.begin():
                result = await db.execute(select(User).where(User.role.in_(["admin", "superadmin"])))
                stats["admin_count"] = len(result.scalars().all())
            weekly_data = await redis_client.get("weekly_history")
            stats["weekly"] = json.loads(weekly_data) if weekly_data else []
            return {"status": "ok", "data": stats}
        return {"status": "error", "message": "No data in Redis"}
    except Exception as e: return {"status": "error", "message": str(e)}

@app.get("/api/bot")
async def get_bot_info(): return {"status": "ok", "data": BOT_INFO}

if __name__ == "__main__": 
    uvicorn.run(app, host="localhost", port=8000)