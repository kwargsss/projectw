import disnake
import mafic

from disnake.ext import commands
from core.player import CustomPlayer


BLACKLIST_WORDS = ["remix", "cover", "bass boost", "slowed", "reverb", "tribute", "karaoke", "караоке", "ремикс", "кавер"]

class MusicCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_original(self, track_title: str) -> bool:
        """Проверяет, нет ли в названии трека запрещенных слов"""
        title_lower = track_title.lower()
        for word in BLACKLIST_WORDS:
            if word in title_lower:
                return False
        return True

    @commands.slash_command(name="музыка", description="Включить трек или добавить в очередь")
    async def play(self, inter: disnake.ApplicationCommandInteraction, request: str = commands.Param(name="название", description="Введите название песни или ссылку")):
        await inter.response.defer(ephemeral=True)

        if not inter.author.voice or not inter.author.voice.channel:
            return await inter.edit_original_response("❌ Ты должен находиться в голосовом канале!")

        if not inter.guild.voice_client:
            player = await inter.author.voice.channel.connect(cls=CustomPlayer)
            await inter.guild.change_voice_state(channel=inter.author.voice.channel, self_deaf=True)
        else:
            player = inter.guild.voice_client
            if player.channel != inter.author.voice.channel:
                return await inter.edit_original_response(f"❌ Я уже занят в канале {player.channel.mention}!")

        player.text_channel = inter.channel

        # --- ЛОГИКА ПОИСКА "ЖЕСТКИЙ ОРИГИНАЛ" ---
        tracks = None
        fallback_track = None 

        if request.startswith("http://") or request.startswith("https://"):
            try:
                tracks = await player.fetch_tracks(request)
            except Exception as e:
                self.bot.logger.error(f"Ошибка при загрузке по ссылке: {e}")
        else:
            search_types = ["ymsearch", "ytsearch", "vksearch"]
            
            for s_type in search_types:
                try:
                    # Пытаемся найти трек
                    found_tracks = await player.fetch_tracks(request, search_type=s_type)
                    
                    if found_tracks:
                        if isinstance(found_tracks, mafic.Playlist):
                            tracks = found_tracks
                            break
                            
                        if not fallback_track:
                            fallback_track = found_tracks[0]

                        for t in found_tracks:
                            if self.is_original(t.title):
                                tracks = [t] 
                                break 
                        
                    if tracks:
                        # Успешно нашли, прерываем каскад
                        break 
                        
                except Exception as e:
                    # Если сервис (например, Яндекс) упал с таймаутом, мы просто ловим ошибку
                    # Пишем в лог и идем к следующему сервису в цикле (YouTube)
                    self.bot.logger.warning(f"Сервис {s_type} недоступен или выдал ошибку: {e}. Пробую следующий...")
                    continue

            if not tracks and fallback_track:
                tracks = [fallback_track]
                await inter.followup.send("⚠️ Чистый оригинал не найден, включено наиболее похожее совпадение.", ephemeral=True)

        # ----------------------------------------

        if not tracks:
            return await inter.edit_original_response("❌ По твоему запросу ничего не найдено.")

        if isinstance(tracks, mafic.Playlist):
            player.cancel_timeout() # <--- ОТМЕНЯЕМ ТАЙМЕР
            for track in tracks.tracks:
                await player.add_to_queue(track)
            
            if not player.current:
                track = await player.play_next()
                await player.update_player_ui(track)
            
            return await inter.edit_original_response(f"✅ Добавлен плейлист **{tracks.name}** ({len(tracks.tracks)} треков).")

        track = tracks[0] if isinstance(tracks, list) else tracks

        if player.current:
            player.cancel_timeout() # <--- ОТМЕНЯЕМ ТАЙМЕР
            await player.add_to_queue(track)
            return await inter.edit_original_response(f"📝 Трек **{track.title}** добавлен в очередь!")
        else:
            player.cancel_timeout() # <--- ОТМЕНЯЕМ ТАЙМЕР
            await player.play(track)
            await player.update_player_ui(track)
            return await inter.edit_original_response("✅ Музыка начала играть!")

def setup(bot):
    bot.add_cog(MusicCommands(bot))