import jwt

from fastapi import Request, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from config import Config
from database import get_db
from models import User

def get_user_from_token(request: Request):
    token = request.cookies.get("access_token")
    if not token: raise HTTPException(status_code=401, detail="Не авторизован")
    try: return jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
    except: raise HTTPException(status_code=401, detail="Токен недействителен")

async def _verify_role(request: Request, db: AsyncSession, allowed_roles: list[str], error_msg: str):
    payload = get_user_from_token(request)
    user_id = int(payload["sub"])
    
    async with db.begin():
        result = await db.execute(select(User).where(User.id == user_id))
        db_user = result.scalars().first()
        if not db_user or db_user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail=error_msg)

        payload["role"] = db_user.role
        payload["username"] = db_user.username
        payload["avatar"] = db_user.avatar_hash
        return payload

async def verify_admin_access(request: Request, db: AsyncSession = Depends(get_db)):
    return await _verify_role(request, db, ["admin", "superadmin"], "Нет прав доступа")

async def verify_superadmin_access(request: Request, db: AsyncSession = Depends(get_db)):
    return await _verify_role(request, db, ["superadmin"], "Требуются права Главного Админа")

async def verify_support_access(request: Request, db: AsyncSession = Depends(get_db)):
    return await _verify_role(request, db, ["support", "admin", "superadmin"], "Нет прав доступа")