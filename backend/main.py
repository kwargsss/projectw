import os
import uvicorn
import aiohttp
import jwt
import json
import asyncio

from pydantic import BaseModel
from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
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

class NotificationConfig(BaseModel):
    enabled: bool = False
    channel_id: str = ""
    embed_type: str = "v1"
    content: Optional[str] = ""
    title: Optional[str] = ""
    description: Optional[str] = ""
    color: Optional[str] = "#5865F2"
    image_url: Optional[str] = ""
    thumbnail_url: Optional[str] = ""
    blocks: List[EmbedBlock] = []

class NotificationSettingsModel(BaseModel):
    welcome: NotificationConfig
    goodbye: NotificationConfig

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

async def verify_admin_access(request: Request, db: AsyncSession):
    payload = get_user_from_token(request)
    user_id = int(payload["sub"])
    async with db.begin():
        result = await db.execute(select(User).where(User.id == user_id))
        db_user = result.scalars().first()
        if not db_user or db_user.role not in ["admin", "superadmin"]:
            raise HTTPException(status_code=403, detail="Нет прав доступа")

        payload["role"] = db_user.role
        payload["username"] = db_user.username
        payload["avatar"] = db_user.avatar_hash
        return payload

async def verify_superadmin_access(request: Request, db: AsyncSession):
    payload = get_user_from_token(request)
    user_id = int(payload["sub"])
    async with db.begin():
        result = await db.execute(select(User).where(User.id == user_id))
        db_user = result.scalars().first()
        if not db_user or db_user.role != "superadmin":
            raise HTTPException(status_code=403, detail="Требуются права Главного Админа")
        
        payload["role"] = db_user.role
        payload["username"] = db_user.username
        payload["avatar"] = db_user.avatar_hash
        return payload

async def verify_support_access(request: Request, db: AsyncSession):
    payload = get_user_from_token(request)
    user_id = int(payload["sub"])
    async with db.begin():
        result = await db.execute(select(User).where(User.id == user_id))
        db_user = result.scalars().first()
        if not db_user or db_user.role not in ["support", "admin", "superadmin"]:
            raise HTTPException(status_code=403, detail="Нет прав доступа")
        
        payload["role"] = db_user.role
        payload["username"] = db_user.username
        payload["avatar"] = db_user.avatar_hash
        return payload

class TicketConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, ticket_id: str):
        await websocket.accept()
        if ticket_id not in self.active_connections:
            self.active_connections[ticket_id] = []
        self.active_connections[ticket_id].append(websocket)

    def disconnect(self, websocket: WebSocket, ticket_id: str):
        if ticket_id in self.active_connections:
            self.active_connections[ticket_id].remove(websocket)

    async def broadcast(self, ticket_id: str, message: dict):
        if ticket_id in self.active_connections:
            for connection in self.active_connections[ticket_id]:
                await connection.send_json(message)

ticket_manager = TicketConnectionManager()

@app.get("/api/tickets")
async def get_all_tickets(request: Request, db: AsyncSession = Depends(get_db)):
    await verify_support_access(request, db)
    
    ticket_keys = await redis_client.keys("ticket:*")
    tickets = []
    
    for key in ticket_keys:
        try:
            key_type = await redis_client.type(key)

            if key_type in [b'hash', 'hash']:
                data = await redis_client.hgetall(key)
                if data:
                    tickets.append(data)
            else:
                logger.warning(f"[Redis] Пропущен ключ {key}, так как его тип {key_type} (ожидался hash).")
        except Exception as e:
            logger.error(f"[Redis] Ошибка при чтении тикета {key}: {e}")
            continue

    def get_sort_key(x):
        try:
            return int(x.get("created_at", 0))
        except (ValueError, TypeError):
            return 0

    tickets.sort(key=get_sort_key, reverse=True)
    return {"status": "ok", "data": tickets}

# ДОБАВЛЕНО: Эндпоинт для загрузки всей истории сообщений тикета
@app.get("/api/tickets/{ticket_id}/messages")
async def get_ticket_messages(ticket_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    await verify_support_access(request, db)
    try:
        messages = await redis_client.lrange(f"ticket_messages:{ticket_id}", 0, -1)
        parsed_messages = [json.loads(m) for m in messages]
        return {"status": "ok", "data": parsed_messages}
    except Exception as e:
        logger.error(f"[ERROR] Ошибка загрузки истории сообщений: {e}")
        return {"status": "error", "data": []}

@app.post("/api/tickets/{ticket_id}/action")
async def manage_ticket_action(ticket_id: str, action: str, request: Request, db: AsyncSession = Depends(get_db)):
    user_info = await verify_support_access(request, db)

    if action == "force_delete":
        await redis_client.delete(f"ticket:{ticket_id}")
        await redis_client.delete(f"transcript:{ticket_id}")
        # ДОБАВЛЕНО: Очистка истории при жестком удалении
        await redis_client.delete(f"ticket_messages:{ticket_id}")
        return {"status": "ok", "message": "Архив безвозвратно удален"}
    
    payload = {
        "action": action,
        "ticket_id": ticket_id,
        "admin_id": user_info["sub"],
        "admin_name": user_info["username"]
    }
    await redis_client.publish("web_ticket_controls", json.dumps(payload))
    return {"status": "ok", "message": f"Команда {action} отправлена"}

@app.get("/api/tickets/{ticket_id}/transcript")
async def get_ticket_transcript(ticket_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    await verify_support_access(request, db)
    transcript = await redis_client.get(f"transcript:{ticket_id}")
    if transcript:
        html_content = transcript.decode('utf-8') if isinstance(transcript, bytes) else transcript
        return HTMLResponse(content=html_content)
    return HTMLResponse(content="<div style='color: white; font-family: sans-serif; text-align: center; padding-top: 50px;'><h2>Транскрипт не найден</h2><p>Возможно, это старый тикет, удаленный до обновления.</p></div>", status_code=404)

@app.post("/api/tickets/{ticket_id}/message")
async def send_ticket_message(ticket_id: str, request: Request, payload: dict, db: AsyncSession = Depends(get_db)):
    user_info = await verify_support_access(request, db)
    
    avatar_url = f"https://cdn.discordapp.com/avatars/{user_info['sub']}/{user_info['avatar']}.png" if user_info.get('avatar') else "https://cdn.discordapp.com/embed/avatars/0.png"
    
    msg_data = {
        "action": "send_message",
        "ticket_id": ticket_id,
        "content": payload.get("content"),
        "author_name": user_info["username"],
        "author_avatar": avatar_url
    }
    
    await redis_client.publish("web_ticket_controls", json.dumps(msg_data))
    return {"status": "ok"}

@app.websocket("/api/ws/tickets/{ticket_id}")
async def websocket_ticket_chat(websocket: WebSocket, ticket_id: str):
    await ticket_manager.connect(websocket, ticket_id)
    
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(f"ticket_chat:{ticket_id}")
    
    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message:
                data = json.loads(message["data"])
                await websocket.send_json(data)
            await asyncio.sleep(0.1)

            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
            except asyncio.TimeoutError:
                pass
    except WebSocketDisconnect:
        ticket_manager.disconnect(websocket, ticket_id)
        await pubsub.unsubscribe(f"ticket_chat:{ticket_id}")

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
    await verify_superadmin_access(request, db)
    async with db.begin():
        stmt = select(User).where(User.role.in_(["admin", "superadmin", "support"]))
        result = await db.execute(stmt)
        return {"status": "ok", "data": [{"id": str(u.id), "username": u.username, "avatar": u.avatar_hash, "role": u.role} for u in result.scalars().all()]}

@app.get("/api/users/search")
async def search_users(request: Request, q: str = "", db: AsyncSession = Depends(get_db)):
    await verify_superadmin_access(request, db)
    if not q or len(q) < 2: return {"status": "ok", "data": []}
    async with db.begin():
        stmt = select(User).where(User.id == int(q)) if q.isdigit() else select(User).where(User.username.ilike(f"%{q}%"))
        result = await db.execute(stmt)
        return {"status": "ok", "data": [{"id": str(u.id), "username": u.username, "avatar": u.avatar_hash, "role": u.role} for u in result.scalars().all()]}

@app.post("/api/users/role")
async def update_user_role(request: Request, data: RoleUpdate, db: AsyncSession = Depends(get_db)):
    admin_payload = await verify_superadmin_access(request, db)
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
async def send_embed_message(request: Request, payload: EmbedStructure, db: AsyncSession = Depends(get_db)):
    admin_info = await verify_admin_access(request, db)
    bot_payload = payload.dict(exclude_none=True)
    avatar_url = f"https://cdn.discordapp.com/avatars/{admin_info['sub']}/{admin_info['avatar']}.png" if admin_info.get('avatar') else "https://cdn.discordapp.com/embed/avatars/0.png"
    bot_payload['footer'] = {"text": f"Отправлено администратором: {admin_info['username']}", "icon_url": avatar_url}
    await redis_client.publish("projectw_embed_commands", json.dumps(bot_payload))
    logger.warning(f"[ACTION] Админ {admin_info['username']} отправил Embed сообщение в канал {payload.channel_id}.")
    return {"status": "ok", "message": "Команда отправлена боту"}

@app.post("/api/embed/send_v2")
@limiter.limit("30/minute") 
async def send_embed_message_v2(request: Request, payload: EmbedV2Structure, db: AsyncSession = Depends(get_db)):
    admin_info = await verify_admin_access(request, db)
    bot_payload = payload.dict(exclude_none=True)
    avatar_url = f"https://cdn.discordapp.com/avatars/{admin_info['sub']}/{admin_info['avatar']}.png" if admin_info.get('avatar') else "https://cdn.discordapp.com/embed/avatars/0.png"
    bot_payload['footer'] = {"text": f"Отправлено администратором: {admin_info['username']}", "icon_url": avatar_url}
    await redis_client.publish("projectw_embed_v2_commands", json.dumps(bot_payload))
    logger.warning(f"[ACTION] Админ {admin_info['username']} отправил V2 Embed в канал {payload.channel_id}.")
    return {"status": "ok", "message": "Команда V2 отправлена боту"}

@app.get("/api/settings/notifications")
@limiter.limit("60/minute")
async def get_notifications(request: Request, db: AsyncSession = Depends(get_db)):
    await verify_admin_access(request, db)
    data = await redis_client.get("notification_settings")
    if data: return {"status": "ok", "data": json.loads(data)}
    default_data = {
        "welcome": {"enabled": False, "channel_id": "", "embed_type": "v1", "color": "#5865F2", "blocks": []},
        "goodbye": {"enabled": False, "channel_id": "", "embed_type": "v1", "color": "#ED4245", "blocks": []}
    }
    return {"status": "ok", "data": default_data}

@app.post("/api/settings/notifications")
@limiter.limit("30/minute")
async def save_notifications(request: Request, payload: NotificationSettingsModel, db: AsyncSession = Depends(get_db)):
    admin_info = await verify_admin_access(request, db)
    await redis_client.set("notification_settings", payload.json())
    logger.warning(f"[ACTION] Админ {admin_info['username']} обновил настройки оповещений (Вход/Выход).")
    return {"status": "ok"}

@app.get("/api/channels")
@limiter.limit("60/minute")
async def get_channels(request: Request, db: AsyncSession = Depends(get_db)):
    await verify_admin_access(request, db)
    data = await redis_client.get("guild_channels")
    return {"status": "ok", "data": json.loads(data) if data else []}

@app.get("/api/stats")
@limiter.limit("60/minute")
async def get_stats(request: Request, db: AsyncSession = Depends(get_db)): 
    await verify_support_access(request, db)
    try:
        data = await redis_client.get("guild_stats")
        if data:
            stats = json.loads(data)
            async with db.begin():
                result = await db.execute(select(User).where(User.role.in_(["admin", "superadmin", "support"])))
                stats["admin_count"] = len(result.scalars().all())
            weekly_data = await redis_client.get("weekly_history")
            stats["weekly"] = json.loads(weekly_data) if weekly_data else []
            return {"status": "ok", "data": stats}
        return {"status": "error", "message": "No data in Redis"}
    except Exception as e: return {"status": "error", "message": str(e)}

@app.get("/api/bot")
async def get_bot_info(): 
    return {"status": "ok", "data": BOT_INFO}

if __name__ == "__main__": 
    uvicorn.run(app, host="localhost", port=8000)