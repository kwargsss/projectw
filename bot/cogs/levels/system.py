import disnake
import time

from disnake.ext import commands
from utils.leveling import (
    get_message_xp, get_voice_xp, get_level_from_xp, 
    get_xp_for_level, generate_progress_bar, MESSAGE_COOLDOWN
)


class LevelingSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if message.author.bot or not message.guild:
            return

        user_id = message.author.id
        cd_key = f"xp_cd:{user_id}"

        if message.author.bot or not message.guild:
            return

        if await self.bot.redis.get(cd_key):
            return
        
        await self.bot.redis.set(cd_key, "1", ex=MESSAGE_COOLDOWN)
        
        await self.bot.redis.hincrby(f"user_stats:{user_id}", "messages", 1)
        xp_gained = get_message_xp()
        
        old_xp = await self.bot.redis.zscore("global_xp", str(user_id))
        old_level = get_level_from_xp(float(old_xp) if old_xp else 0.0)

        new_xp = await self.bot.redis.zincrby("global_xp", xp_gained, str(user_id))
        new_level = get_level_from_xp(float(new_xp))

        if new_level > old_level:
            embed = disnake.Embed(
                title="🎉 Уровень повышен!",
                description=f"{message.author.mention}, ты достиг **{new_level} уровня**!",
                color=disnake.Color.purple()
            )
            try: await message.channel.send(embed=embed, delete_after=10)
            except disnake.Forbidden: pass

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: disnake.Member, before: disnake.VoiceState, after: disnake.VoiceState):
        if member.bot: return
        user_id = member.id
        join_key = f"voice_join:{user_id}"

        if before.channel is None and after.channel is not None:
            await self.bot.redis.set(join_key, int(time.time()))

        elif before.channel is not None and after.channel is None:
            join_time = await self.bot.redis.get(join_key)
            if join_time:
                minutes_spent = (int(time.time()) - int(join_time)) // 60
                await self.bot.redis.delete(join_key)

                if minutes_spent > 0:
                    await self.bot.redis.hincrby(f"user_stats:{user_id}", "voice_mins", minutes_spent)
                    xp_gained = get_voice_xp(minutes_spent)
                    await self.bot.redis.zincrby("global_xp", xp_gained, str(user_id))

    @commands.slash_command(name="ранг", description="Посмотреть уровень")
    async def rank(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member = None):
        target = member or inter.author
        user_id = target.id

        xp = await self.bot.redis.zscore("global_xp", str(user_id))
        if not xp:
            await inter.response.send_message(f"У {target.mention} пока нет опыта.", ephemeral=True)
            return

        xp = float(xp)
        level = get_level_from_xp(xp)
        
        rank_index = await self.bot.redis.zrevrank("global_xp", str(user_id))
        rank_display = rank_index + 1 if rank_index is not None else "?"

        stats = await self.bot.redis.hgetall(f"user_stats:{user_id}")
        messages = stats.get(b"messages", b"0").decode() if isinstance(stats.get(b"messages"), bytes) else stats.get("messages", "0")
        voice_mins = stats.get(b"voice_mins", b"0").decode() if isinstance(stats.get(b"voice_mins"), bytes) else stats.get("voice_mins", "0")

        embed = disnake.Embed(color=target.color or disnake.Color.purple())
        embed.set_author(name=f"Статистика: {target.display_name}", icon_url=target.display_avatar.url)
        embed.add_field(name="Ранг", value=f"🏆 **#{rank_display}**", inline=False)
        embed.add_field(name="Уровень", value=f"**{level}**", inline=True)
        embed.add_field(name="Опыт", value=f"**{int(xp)}** / {get_xp_for_level(level + 1)}", inline=True)
        embed.add_field(name="Прогресс", value=f"`{generate_progress_bar(xp, level)}`", inline=False)
        embed.add_field(name="Сообщений", value=f"💬 {messages}", inline=True)
        embed.add_field(name="В войсе", value=f"🎙️ {voice_mins} мин", inline=True)
        
        await inter.response.send_message(embed=embed)

    @commands.slash_command(name="лидеры", description="Топ-10 сервера")
    async def leaderboard(self, inter: disnake.ApplicationCommandInteraction):
        top_users = await self.bot.redis.zrevrange("global_xp", 0, 9, withscores=True)
        if not top_users:
            await inter.response.send_message("Таблица лидеров пуста.", ephemeral=True)
            return

        embed = disnake.Embed(title="🏆 Топ активных участников", color=disnake.Color.gold())
        desc = ""
        for i, (uid_b, xp_b) in enumerate(top_users, 1):
            uid = uid_b.decode() if isinstance(uid_b, bytes) else uid_b
            xp = float(xp_b)
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"**{i}.**"
            desc += f"{medal} <@{uid}> — **Ур. {get_level_from_xp(xp)}** ({int(xp)} XP)\n"

        embed.description = desc
        await inter.response.send_message(embed=embed)

def setup(bot):
    bot.add_cog(LevelingSystem(bot))