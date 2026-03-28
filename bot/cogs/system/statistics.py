import disnake
import json
import asyncio

from datetime import datetime
from disnake.ext import commands, tasks

class StatisticsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_stats_cache.start()

    def cog_unload(self):
        self.update_stats_cache.cancel()

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if not message.author.bot: 
            try:
                await asyncio.wait_for(self.bot.redis.incr("stats_messages_24h"), timeout=1.0)
            except: pass

    @commands.Cog.listener("on_application_command")
    async def stats_command_tracker(self, inter: disnake.ApplicationCommandInteraction):
        try:
            await asyncio.wait_for(self.bot.redis.incr("stats_commands_24h"), timeout=1.0)
        except: pass

    @tasks.loop(seconds=5)
    async def update_stats_cache(self):
        if not self.bot.guilds: return
        guild = self.bot.guilds[0]
        
        msg_count = await self.bot.redis.get("stats_messages_24h")
        cmd_count = await self.bot.redis.get("stats_commands_24h")
        online_count = sum(1 for m in guild.members if m.status != disnake.Status.offline)

        text_channels = [{"id": str(c.id), "name": c.name} for c in guild.text_channels]
        await self.bot.redis.set("guild_channels", json.dumps(text_channels), ex=30)

        today_str = datetime.now().strftime("%d.%m")
        history_str = await self.bot.redis.get("weekly_history")
        history = json.loads(history_str) if history_str else []

        if not history or history[-1]["date"] != today_str:
            await self.bot.redis.set("stats_messages_24h", 0)
            await self.bot.redis.set("stats_commands_24h", 0)
            msg_count = cmd_count = 0
            self.bot.logger.info(f"[STATS] Наступил новый день ({today_str})! Суточная статистика сброшена.")
            if len(history) >= 7: history.pop(0)
            history.append({"date": today_str, "messages": 0, "commands": 0})

        history[-1]["messages"] = int(msg_count) if msg_count else 0
        history[-1]["commands"] = int(cmd_count) if cmd_count else 0
        await self.bot.redis.set("weekly_history", json.dumps(history))

        stats = { 
            "name": guild.name, 
            "member_count": guild.member_count, 
            "online": online_count, 
            "messages_24h": int(msg_count) if msg_count else 0, 
            "commands_24h": int(cmd_count) if cmd_count else 0 
        }
        await self.bot.redis.set("guild_stats", json.dumps(stats), ex=30)

    @update_stats_cache.before_loop
    async def before_update_stats_cache(self):
        await self.bot.wait_until_ready()

def setup(bot):
    bot.add_cog(StatisticsCog(bot))