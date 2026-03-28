import disnake

from disnake.ext import commands
from config import Config

def is_admin(member: disnake.Member) -> bool:
    if member.guild_permissions.administrator:
        return True
        
    role_ids = [role.id for role in member.roles]
    return Config.ADMIN_ROLE_ID in role_ids

def is_staff(member: disnake.Member) -> bool:
    if is_admin(member):
        return True
        
    role_ids = [role.id for role in member.roles]
    return Config.SUPPORT_ROLE_ID in role_ids

def admin_only():
    async def predicate(ctx_or_inter):
        if is_admin(ctx_or_inter.author):
            return True

        raise commands.CheckFailure("У вас нет прав администратора для использования этой команды.")
    
    return commands.check(predicate)

def staff_only():
    async def predicate(ctx_or_inter):
        if is_staff(ctx_or_inter.author):
            return True
            
        raise commands.CheckFailure("У вас нет прав персонала для использования этой команды.")
    
    return commands.check(predicate)