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
        author = ctx_or_inter.author
        if is_admin(author):
            return True
        
        if isinstance(ctx_or_inter, disnake.Interaction):
            await ctx_or_inter.response.send_message("❌ У вас нет прав администратора для использования этой команды.", ephemeral=True)
            return False
            
        raise commands.CheckFailure("Требуются права администратора.")
    
    return commands.check(predicate)

def staff_only():
    async def predicate(ctx_or_inter):
        author = ctx_or_inter.author
        if is_staff(author):
            return True
            
        if isinstance(ctx_or_inter, disnake.Interaction):
            await ctx_or_inter.response.send_message("❌ У вас нет прав персонала для использования этой команды.", ephemeral=True)
            return False
            
        raise commands.CheckFailure("Требуются права персонала.")
    
    return commands.check(predicate)