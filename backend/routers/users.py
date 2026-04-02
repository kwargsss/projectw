import shutil
import uuid 
import os

from fastapi import APIRouter, Request, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from config import Config
from database import get_db, redis_client, AsyncSessionLocal
from models import User
from schemas import RoleUpdate
from dependencies import verify_superadmin_access
from core.logger import setup_logger


router = APIRouter(prefix="/api", tags=["Users"])
logger = setup_logger("backend", Config.TG_BOT_TOKEN, Config.TG_CHAT_ID)

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UPLOAD_DIR = os.path.join(BACKEND_DIR, "uploads", "backgrounds")

@router.get("/admins/list")
async def get_admins_list(request: Request, db: AsyncSession = Depends(get_db)):
    await verify_superadmin_access(request, db)
    async with db.begin():
        stmt = select(User).where(User.role.in_(["admin", "superadmin", "support"]))
        result = await db.execute(stmt)
        return {"status": "ok", "data": [{"id": str(u.id), "username": u.username, "avatar": u.avatar_hash, "role": u.role} for u in result.scalars().all()]}

@router.get("/users/search")
async def search_users(request: Request, q: str = "", db: AsyncSession = Depends(get_db)):
    await verify_superadmin_access(request, db)
    if not q or len(q) < 2: return {"status": "ok", "data": []}
    async with db.begin():
        stmt = select(User).where(User.id == int(q)) if q.isdigit() else select(User).where(User.username.ilike(f"%{q}%"))
        result = await db.execute(stmt)
        return {"status": "ok", "data": [{"id": str(u.id), "username": u.username, "avatar": u.avatar_hash, "role": u.role} for u in result.scalars().all()]}

@router.post("/users/role")
async def update_user_role(request: Request, data: RoleUpdate, db: AsyncSession = Depends(get_db)):
    admin_payload = await verify_superadmin_access(request, db)
    if data.user_id == Config.ADMIN_DISCORD_ID: raise HTTPException(status_code=400, detail="Нельзя изменить роль создателя")
    async with db.begin():
        result = await db.execute(select(User).where(User.id == data.user_id))
        db_user = result.scalars().first()
        if not db_user: raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        logger.warning(f"[SECURITY] {admin_payload['username']} {'выдал админку' if data.role == 'admin' else 'снял админку у'} {db_user.username} (ID: {db_user.id}).")
        db_user.role = data.role
    return {"status": "ok"}

@router.post("/users/{user_id}/background")
async def upload_user_background(user_id: int, file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Можно загрузить только изображение")
        
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    async with AsyncSessionLocal() as db:
        async with db.begin():
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalars().first()
            
            if user:
                if user.background_file:
                    old_filepath = os.path.join(UPLOAD_DIR, user.background_file)
                    if os.path.exists(old_filepath):
                        try:
                            os.remove(old_filepath)
                        except Exception as e:
                            logger.error(f"[UPLOAD] Не удалось удалить старый фон {old_filepath}: {e}")

                ext = file.filename.split('.')[-1]
                filename = f"bg_{user_id}_{uuid.uuid4().hex[:6]}.{ext}"
                filepath = os.path.join(UPLOAD_DIR, filename)
                
                with open(filepath, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                    
                user.background_file = filename
                
    await redis_client.set(f"user_bg:{user_id}", filename)
    
    return {"status": "ok", "message": "Фон успешно обновлен"}

@router.delete("/users/{user_id}/background")
async def delete_user_background(user_id: int):
    async with AsyncSessionLocal() as db:
        async with db.begin():
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalars().first()
            
            if not user:
                raise HTTPException(status_code=404, detail="Пользователь не найден")
                
            if user.background_file:
                filepath = os.path.join(UPLOAD_DIR, user.background_file)
                if os.path.exists(filepath):
                    try:
                        os.remove(filepath)
                    except Exception as e:
                        logger.error(f"[DELETE] Не удалось удалить фон {filepath}: {e}")
                
                user.background_file = None
                
    await redis_client.delete(f"user_bg:{user_id}")
    
    return {"status": "ok", "message": "Фон успешно удален"}