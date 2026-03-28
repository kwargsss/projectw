import jwt

from fastapi import Request, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from config import Config
from database import get_db

def get_user_from_token(request: Request):
    token = request.cookies.get("access_token")
    if not token: 
        raise HTTPException(status_code=401, detail="Не авторизован")
    try: 
        return jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Срок действия токена истек")
    except jwt.PyJWTError: 
        raise HTTPException(status_code=401, detail="Токен недействителен")

async def _verify_role(request: Request, allowed_roles: list[str], error_msg: str):
    payload = get_user_from_token(request)
    
    user_role = payload.get("role")
    if not user_role or user_role not in allowed_roles:
        raise HTTPException(status_code=403, detail=error_msg)

    return payload

async def verify_admin_access(request: Request, db: AsyncSession = Depends(get_db)):
    return await _verify_role(request, ["admin", "superadmin"], "Нет прав доступа")

async def verify_superadmin_access(request: Request, db: AsyncSession = Depends(get_db)):
    return await _verify_role(request, ["superadmin"], "Требуются права Главного Админа")

async def verify_support_access(request: Request, db: AsyncSession = Depends(get_db)):
    return await _verify_role(request, ["support", "admin", "superadmin"], "Нет прав доступа")