import disnake

def format_text(text: str, member: disnake.Member) -> str:
    if not text: 
        return ""
    
    return text.replace("{user}", member.mention)\
               .replace("{user.name}", member.name)\
               .replace("{server}", member.guild.name)\
               .replace("{count}", str(member.guild.member_count))