import disnake
import mafic
import json

from disnake.ext import commands


BLACKLIST_WORDS = ["remix", "cover", "bass boost", "slowed", "reverb", "tribute", "karaoke", "караоке", "ремикс", "кавер"]

class MusicCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_worker_for_channel(self, guild_id: int, voice_channel_id: int):
        vc_worker = await self.bot.redis.get(f"vc_worker:{voice_channel_id}")
        if vc_worker:
            return vc_worker.decode('utf-8') if isinstance(vc_worker, bytes) else vc_worker

        active_in_guild = await self.bot.redis.smembers(f"guild_active_workers:{guild_id}")
        active_in_guild = {w.decode('utf-8') if isinstance(w, bytes) else w for w in active_in_guild}

        all_workers = await self.bot.redis.smembers("all_workers")
        all_workers = {w.decode('utf-8') if isinstance(w, bytes) else w for w in all_workers}

        available_workers = list(all_workers - active_in_guild)

        if not available_workers:
            return None

        chosen_worker = available_workers[0]

        await self.bot.redis.set(f"vc_worker:{voice_channel_id}", chosen_worker)
        await self.bot.redis.sadd(f"guild_active_workers:{guild_id}", chosen_worker)

        return chosen_worker

    def is_original(self, track_title: str) -> bool:
        title_lower = track_title.lower()
        for word in BLACKLIST_WORDS:
            if word in title_lower: return False
        return True

    @commands.slash_command(name="музыка", description="Включить трек или добавить в очередь")
    async def play(self, inter: disnake.ApplicationCommandInteraction, request: str = commands.Param(name="название", description="Введите название песни или ссылку")):
        await inter.response.defer(ephemeral=True)

        if not inter.author.voice or not inter.author.voice.channel:
            return await inter.edit_original_response("❌ Вы должны находиться в голосовом канале!")

        voice_channel_id = inter.author.voice.channel.id
        worker_id = await self.get_worker_for_channel(inter.guild.id, voice_channel_id)
        
        if not worker_id:
            return await inter.edit_original_response("❌ Достигнут лимит музыкальных ботов. Все боты уже заняты в других каналах этого сервера!")

        node = self.bot.pool.nodes[0]
        tracks, fallback_track = None, None 

        if request.startswith("http://") or request.startswith("https://"):
            try: tracks = await node.fetch_tracks(request)
            except: pass
        else:
            for s_type in ["ymsearch", "ytsearch", "vksearch"]:
                try:
                    found_tracks = await node.fetch_tracks(request, search_type=s_type)
                    if found_tracks:
                        if isinstance(found_tracks, mafic.Playlist):
                            tracks = found_tracks
                            break
                        if not fallback_track: fallback_track = found_tracks[0]
                        for t in found_tracks:
                            if self.is_original(t.title):
                                tracks = [t] 
                                break 
                    if tracks: break 
                except: continue
            if not tracks and fallback_track:
                tracks = [fallback_track]
                await inter.followup.send("⚠️ Чистый оригинал не найден, включено похожее совпадение.", ephemeral=True)

        if not tracks:
            return await inter.edit_original_response("❌ По твоему запросу ничего не найдено.")

        queue_key = f"music:queue:{voice_channel_id}"
        
        if isinstance(tracks, mafic.Playlist):
            for track in tracks.tracks:
                await self.bot.redis.rpush(queue_key, track.id)
            track_msg = f"плейлист **{tracks.name}** ({len(tracks.tracks)} треков)"
        else:
            track = tracks[0] if isinstance(tracks, list) else tracks
            await self.bot.redis.rpush(queue_key, track.id)
            track_msg = f"трек **{track.title}**"

        payload = {
            "action": "connect_and_play",
            "guild_id": inter.guild.id,
            "voice_channel_id": voice_channel_id,
            "text_channel_id": inter.channel.id
        }

        await self.bot.redis.set(f"vc_text_channel:{voice_channel_id}", inter.channel.id)

        payload = {
            "action": "connect_and_play",
            "guild_id": inter.guild.id,
            "voice_channel_id": voice_channel_id,
        }
        await self.bot.redis.publish(f"worker_cmd:{worker_id}", json.dumps(payload))

        await inter.edit_original_response(f"✅ Успешно! Передал {track_msg} музыкальному боту.")

def setup(bot):
    bot.add_cog(MusicCommands(bot))