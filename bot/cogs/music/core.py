import mafic
import disnake

from disnake.ext import commands
from config import Config


class MusicCore(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.pool = mafic.NodePool(self.bot)
        self.bot.loop.create_task(self.connect_nodes())

    async def connect_nodes(self):
        await self.bot.wait_until_ready()
        await self.bot.pool.create_node(
            host=Config.LAVALINK_HOST,
            port=Config.LAVALINK_PORT,
            label="MAIN_NODE",
            password=Config.LAVALINK_PASSWORD,
        )

    @commands.Cog.listener()
    async def on_node_ready(self, node: mafic.Node):
        self.bot.logger.info(f"🎵 [MUSIC] Lavalink Node '{node.label}' успешно подключена!")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: disnake.Member, before: disnake.VoiceState, after: disnake.VoiceState):
        player = getattr(member.guild, "voice_client", None)
        if not player:
            return
            
        if member == self.bot.user and before.channel is not None and after.channel is None:
            queue_key = f"music:queue:{member.guild.id}"
            await self.bot.redis.delete(queue_key)
            if hasattr(player, "message") and player.message:
                try:
                    await player.message.delete()
                    player.message = None
                except: pass
            return

        if player.channel:
            non_bot_members = [m for m in player.channel.members if not m.bot]
            
            if not non_bot_members:
                player.cancel_timeout()
                player.timeout_task = self.bot.loop.create_task(player.start_timeout(60))
                if player.text_channel:
                    try: await player.text_channel.send("В голосовом канале никого нет. Уйду через 1 минуту 💤", delete_after=60)
                    except: pass
            else:
                if getattr(player, "timeout_task", None):
                    player.cancel_timeout()
                    if not player.current:
                        player.timeout_task = self.bot.loop.create_task(player.start_timeout(300))

    @commands.Cog.listener()
    async def on_track_end(self, event: mafic.TrackEndEvent):
        player = event.player
        reason = str(event.reason).upper()
        
        if "FINISHED" in reason or "STOPPED" in reason or "FAILED" in reason:
            if "FINISHED" in reason:
                if player.loop_mode == 1:
                    await player.redis.lpush(player.queue_key, event.track.id)
                elif player.loop_mode == 2:
                    await player.redis.rpush(player.queue_key, event.track.id)

                try:
                    track_name = f"{event.track.author} - {event.track.title}"[:200]
                    
                    await player.redis.zincrby(f"music_top:guild:{player.guild.id}", 1, track_name)
                    
                    if player.channel:
                        for member in player.channel.members:
                            if not member.bot:
                                await player.redis.zincrby(f"music_top:user:{member.id}", 1, track_name)
                                
                except Exception as e:
                    print(f"[STATS ERROR] Ошибка записи статистики: {e}")

            next_track = await player.play_next(finished_track=event.track)
            
            if next_track:
                player.cancel_timeout()
                await player.update_player_ui(next_track)
            else:
                if player.autopilot and ("FINISHED" in reason or "STOPPED" in reason or "FAILED" in reason):
                    
                    ap_track = await player.play_autopilot(event.track)
                    
                    if ap_track:
                        player.cancel_timeout()
                        await player.update_player_ui(ap_track)
                        return

                await player.update_player_ui(None)
                player.timeout_task = self.bot.loop.create_task(player.start_timeout(300))

def setup(bot):
    bot.add_cog(MusicCore(bot))