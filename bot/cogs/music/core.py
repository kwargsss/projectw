import mafic
import disnake
import json

from disnake.ext import commands
from config import Config
from ui.music_ui import MusicPlayerView


class MusicCore(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.pool = mafic.NodePool(self.bot)
        self.bot.loop.create_task(self.connect_nodes())
        self.bot.loop.create_task(self.listen_master_events())

    async def connect_nodes(self):
        await self.bot.wait_until_ready()
        await self.bot.pool.create_node(
            host=Config.LAVALINK_HOST,
            port=Config.LAVALINK_PORT,
            label="MASTER_NODE",
            password=Config.LAVALINK_PASSWORD,
        )

    @commands.Cog.listener()
    async def on_node_ready(self, node: mafic.Node):
        self.bot.logger.info(f"🎵 [MASTER] Lavalink готова к поиску треков!")

    async def listen_master_events(self):
        await self.bot.wait_until_ready()
        pubsub = self.bot.redis.pubsub()
        await pubsub.subscribe("master_events")
        
        async for message in pubsub.listen():
            if message['type'] == 'message':
                try:
                    data = json.loads(message['data'])
                    if data["event"] == "update_ui":
                        await self.handle_ui_update(data)
                    elif data["event"] == "teardown":
                        await self.handle_teardown(data)
                except Exception as e:
                    self.bot.logger.error(f"Ошибка UI Listener: {e}")

    async def handle_ui_update(self, data: dict):
        guild = self.bot.get_guild(data["guild_id"])
        voice_channel_id = data["voice_channel_id"]
        if not guild: return
        
        text_channel_id = await self.bot.redis.get(f"vc_text_channel:{voice_channel_id}")
        if not text_channel_id: return
        
        channel = guild.get_channel(int(text_channel_id))
        if not channel: return

        track = data.get("track")
        if not track:
            embed = disnake.Embed(title="🎶 Очередь закончилась", description="Добавьте новую музыку 💤", color=0x2b2d31)
        else:
            embed = disnake.Embed(title="🎶 Сейчас играет", description=f"**[{track['title']}]({track['uri']})**", color=0x2b2d31)
            embed.add_field(name="👤 Автор", value=track['author'], inline=True)
            minutes, seconds = divmod(track['length'] // 1000, 60)
            embed.add_field(name="⏱️ Длительность", value=f"{minutes:02d}:{seconds:02d}", inline=True)
            
            loop_status = ["Выкл", "🔂 Трек", "🔁 Очередь"][data['loop_mode']]
            embed.add_field(name="🔄 Повтор", value=loop_status, inline=True)
            embed.add_field(name="🛸 Моя Волна(Test)", value="Вкл 🛸" if data['autopilot'] else "Выкл", inline=True)
            embed.add_field(name="📍 Привязан к каналу", value=f"<#{voice_channel_id}>", inline=True)

            if track['artwork_url']:
                embed.set_thumbnail(url=track['artwork_url'])

        view = MusicPlayerView(
            bot=self.bot, guild_id=guild.id, 
            voice_channel_id=voice_channel_id, worker_id=data["worker_id"],
            loop_mode=data["loop_mode"], autopilot=data["autopilot"],
            is_paused=data.get("is_paused", False)
        )

        msg_id = await self.bot.redis.get(f"player_msg:{voice_channel_id}")
        if msg_id:
            try:
                msg = await channel.fetch_message(int(msg_id))
                return await msg.edit(embed=embed, view=view)
            except disnake.NotFound: pass 

        msg = await channel.send(embed=embed, view=view)
        await self.bot.redis.set(f"player_msg:{voice_channel_id}", msg.id)

    async def handle_teardown(self, data: dict):
        guild = self.bot.get_guild(data["guild_id"])
        voice_channel_id = data.get("voice_channel_id")
        if not guild or not voice_channel_id: return
        
        text_channel_id = await self.bot.redis.get(f"vc_text_channel:{voice_channel_id}")
        msg_id = await self.bot.redis.get(f"player_msg:{voice_channel_id}")
        
        if text_channel_id and msg_id:
            channel = guild.get_channel(int(text_channel_id))
            if channel:
                try:
                    msg = await channel.fetch_message(int(msg_id))
                    await msg.delete()
                except: pass
                
        await self.bot.redis.delete(f"player_msg:{voice_channel_id}")
        await self.bot.redis.delete(f"vc_text_channel:{voice_channel_id}")

def setup(bot):
    bot.add_cog(MusicCore(bot))