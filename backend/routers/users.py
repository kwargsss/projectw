from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from config import Config
from database import get_db
from models import User
from schemas import RoleUpdate
from dependencies import verify_superadmin_access
from core.logger import setup_logger

router = APIRouter(prefix="/api", tags=["Users"])
logger = setup_logger("backend", Config.TG_BOT_TOKEN, Config.TG_CHAT_ID)

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