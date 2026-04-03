import disnake

from disnake.ext import commands


class MusicStatistics(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="топ", description="Топ прослушиваемых треков")
    async def top_group(self, inter):
        pass

    @top_group.sub_command(name="сервер", description="Топ-10 треков сервера")
    async def top_server(self, inter: disnake.ApplicationCommandInteraction):
        await self._send_top(inter, f"music_top:guild:{inter.guild.id}", f"🏆 Топ-10 сервера {inter.guild.name}")

    @top_group.sub_command(name="личный", description="Твои топ-10 треков")
    async def top_personal(self, inter: disnake.ApplicationCommandInteraction):
        await self._send_top(inter, f"music_top:user:{inter.author.id}", "🎧 Твой личный топ-10")

    async def _send_top(self, inter, key, title):
        await inter.response.defer()
        
        top_tracks = await self.bot.redis.zrevrange(key, 0, 9, withscores=True)
        
        if not top_tracks:
            return await inter.edit_original_response("📭 Статистика пока пуста. Включите музыку, чтобы начать сбор!")

        desc = ""
        for i, (track_bytes, score) in enumerate(top_tracks, 1):
            track_name = track_bytes.decode('utf-8') if isinstance(track_bytes, bytes) else track_bytes
            count = int(score)
            
            if i == 1: emoji = "🥇"
            elif i == 2: emoji = "🥈"
            elif i == 3: emoji = "🥉"
            else: emoji = "▫️"
            
            desc += f"{emoji} **{track_name}** — `{count} раз(а)`\n"

        embed = disnake.Embed(title=title, description=desc, color=0x2b2d31)
        await inter.edit_original_response(embed=embed)

def setup(bot):
    bot.add_cog(MusicStatistics(bot))