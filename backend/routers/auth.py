import aiohttp
import jwt

from datetime import datetime, timedelta
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from config import Config
from database import get_db
from models import User
from dependencies import get_user_from_token
from core.limiter import limiter
from core.logger import setup_logger

router = APIRouter(prefix="/api/auth", tags=["Auth"])
logger = setup_logger("backend", Config.TG_BOT_TOKEN, Config.TG_CHAT_ID)

@router.get("/login")
@limiter.limit("5/minute")
async def auth_login(request: Request):
    auth_url = f"https://discord.com/oauth2/authorize?client_id={Config.DISCORD_CLIENT_ID}&redirect_uri={Config.DISCORD_REDIRECT_URI}&response_type=code&scope=identify guilds"
    return {"url": auth_url}

@router.get("/callback")
@limiter.limit("5/minute")
async def auth_callback(request: Request, code: str, db: AsyncSession = Depends(get_db)):
    if not code: raise HTTPException(status_code=400, detail="Code not provided")
    
    async with aiohttp.ClientSession() as session:
        data = { 'client_id': Config.DISCORD_CLIENT_ID, 'client_secret': Config.DISCORD_CLIENT_SECRET, 'grant_type': 'authorization_code', 'code': code, 'redirect_uri': Config.DISCORD_REDIRECT_URI }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        async with session.post(Config.TOKEN_URL, data=data, headers=headers) as response:
            token_data = await response.json()
            if 'error' in token_data: 
                return RedirectResponse(url=f"{Config.FRONTEND_URL}/login?error=oauth_failed")
            access_token = token_data['access_token']

        headers = {'Authorization': f'Bearer {access_token}'}
        async with session.get(f"{Config.API_BASE_URL}/users/@me", headers=headers) as response:
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
            if discord_id == Config.ADMIN_DISCORD_ID and db_user.role != "superadmin": db_user.role = "superadmin"
        else:
            is_new = True
            new_role = "superadmin" if discord_id == Config.ADMIN_DISCORD_ID else "user"
            db_user = User(id=discord_id, username=user_info['username'], discriminator=user_info['discriminator'], avatar_hash=user_info.get('avatar'), role=new_role)
            db.add(db_user)
            
    if is_new: logger.info(f"[AUTH] Новый пользователь: {db_user.username} (ID: {db_user.id})")
    else: logger.info(f"[AUTH] Вход: {db_user.username} (Роль: {db_user.role})")

    token_payload = { "sub": str(db_user.id), "username": db_user.username, "avatar": db_user.avatar_hash, "role": db_user.role, "exp": datetime.utcnow() + timedelta(days=7) }
    token = jwt.encode(token_payload, Config.JWT_SECRET, algorithm="HS256")

    response = RedirectResponse(url=f"{Config.FRONTEND_URL}/")
    response.set_cookie(key="access_token", value=token, httponly=True, secure=False, samesite="lax", max_age=7*24*3600)
    return response

@router.get("/me")
async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)):
    payload = get_user_from_token(request)
    async with db.begin():
        result = await db.execute(select(User).where(User.id == int(payload["sub"])))
        db_user = result.scalars().first()
        if not db_user: raise HTTPException(status_code=401, detail="Пользователь не найден")
        return {"id": str(db_user.id), "username": db_user.username, "avatar": db_user.avatar_hash, "role": db_user.role}

@router.post("/logout")
async def logout(request: Request):
    try: logger.info(f"[AUTH] Выход: {get_user_from_token(request)['username']}.")
    except: pass
    response = JSONResponse(content={"status": "ok"})
    response.delete_cookie("access_token")
    return response