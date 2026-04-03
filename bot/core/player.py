import mafic
import disnake
import asyncio
import random

from config import Config
from yandex_music import ClientAsync
from ui.music_ui import MusicPlayerView


class CustomPlayer(mafic.Player):
    def __init__(self, client: disnake.Client, channel: disnake.VoiceChannel):
        super().__init__(client, channel)
        self.redis = self.client.redis
        self.queue_key = f"music:queue:{self.guild.id}"
        self.history_key = f"music:history:{self.guild.id}"
        
        self.message = None 
        self.text_channel = None 
        self.loop_mode = 0 
        self.timeout_task = None 
        
        self.autopilot = False 
        ym_token = Config.YANDEX_TOKEN
        self.ym_client = ClientAsync(token=ym_token)

    async def play_autopilot(self, finished_track: mafic.Track):
        """Умный поиск похожих треков (МОЯ ВОЛНА + ЖЕСТКАЯ ЗАЩИТА ОТ ПОВТОРОВ)"""
        import re
        
        # Функция для очистки текста (оставляет только буквы и цифры для точного сравнения)
        def clean_text(text):
            return re.sub(r'[^a-zа-яё0-9]', '', str(text).lower())

        try:
            if not getattr(self.ym_client, 'me', None):
                try: await self.ym_client.init()
                except: pass

            track_id = None
            if finished_track.source == "yandex":
                track_id = finished_track.identifier
            else:
                search = await self.ym_client.search(f"{finished_track.author} {finished_track.title}", type_="track")
                if search.tracks and search.tracks.results:
                    track_id = search.tracks.results[0].id

            if not track_id: return None

            tracks_list = []
            try:
                # Врубаем нейросеть Яндекса (Мою Волну)
                station = await self.ym_client.rotor_station_tracks(f"track:{track_id}")
                if station and hasattr(station, 'sequence'):
                    tracks_list = [getattr(item, 'track', item) for item in station.sequence]
            except Exception:
                pass

            if not tracks_list:
                try:
                    station = await self.ym_client.rotor_station_tracks("user:onyourwave")
                    if station and hasattr(station, 'sequence'):
                        tracks_list = [getattr(item, 'track', item) for item in station.sequence]
                except Exception:
                    return None

            if not tracks_list: return None

            # 1. Собираем историю ИСКЛЮЧИТЕЛЬНО по названиям (счищая мусор и фиты)
            history = await self.redis.lrange(self.history_key, 0, 40)
            history_titles = []
            for h_id in history:
                try:
                    dec = await self.node.decode_track(h_id)
                    history_titles.append(clean_text(dec.title))
                except: pass

            # Очищаем название трека, который только что играл
            finished_title_clean = clean_text(finished_track.title)

            BLACKLIST = ["remix", "cover", "bass", "slowed", "reverb", "tribute", "karaoke", "караоке", "ремикс", "кавер", "sped up", "speed up", "tiktok", "mashup", "мэшап"]

            track_to_play = None
            
            for t in tracks_list:
                try:
                    if not t.artists: continue
                        
                    title_lower = t.title.lower()
                    if any(word in title_lower for word in BLACKLIST): continue
                        
                    # Очищаем название предложенного трека
                    clean_t_title = clean_text(t.title)
                    
                    # ЖЕСТКАЯ ЗАЩИТА: Сравниваем только чистые названия (БЕЗ АВТОРОВ)
                    # Если название совпадает с тем, что только что играло ИЛИ было в истории - СКИП!
                    if clean_t_title == finished_title_clean: continue
                    if clean_t_title in history_titles: continue

                    # Если трек прошел проверку, формируем запрос для Lavalink
                    artist_name = t.artists[0].name
                    track_to_play = f"{artist_name} {t.title}"
                    break 
                except Exception:
                    continue

            if not track_to_play: return None

            resolved = await self.fetch_tracks(track_to_play, search_type="ymsearch")
            if resolved:
                track = resolved[0] if isinstance(resolved, list) else resolved
                await self.play(track, start_time=0)
                return track

        except Exception as e:
            print(f"Ошибка в автопилоте: {e}")
            return None
        
    # --- ОСТАЛЬНОЙ КОД (без изменений) ---
    async def start_timeout(self, timeout_seconds: int):
        try:
            await asyncio.sleep(timeout_seconds)
            self.timeout_task = None 
            if self.text_channel:
                try: await self.text_channel.send("💤 Я покинул канал из-за неактивности.", delete_after=15)
                except: pass
            await self.destroy() 
        except asyncio.CancelledError:
            pass

    def cancel_timeout(self):
        if self.timeout_task and not self.timeout_task.done():
            self.timeout_task.cancel()

    async def add_to_queue(self, track: mafic.Track):
        await self.redis.rpush(self.queue_key, track.id)

    async def play_next(self, finished_track: mafic.Track = None):
        if finished_track:
            await self.redis.lpush(self.history_key, finished_track.id)
            await self.redis.ltrim(self.history_key, 0, 19)

        track_id = await self.redis.lpop(self.queue_key)
        if not track_id: return None 
            
        track = await self.node.decode_track(track_id)
        await self.play(track, start_time=0) 
        return track

    async def play_previous(self):
        track_id = await self.redis.lpop(self.history_key)
        if not track_id: return None
        
        if self.current:
            await self.redis.lpush(self.queue_key, self.current.id)
            
        track = await self.node.decode_track(track_id)
        await self.play(track, start_time=0) 
        return track

    async def update_player_ui(self, track: mafic.Track = None):
        if not track:
            embed = disnake.Embed(
                title="🎶 Очередь закончилась", 
                description="Добавьте новую музыку, иначе я выйду через 5 минут 💤", 
                color=0x2b2d31
            )
        else:
            embed = disnake.Embed(title="🎶 Сейчас играет", description=f"**[{track.title}]({track.uri})**", color=0x2b2d31)
            embed.add_field(name="👤 Автор", value=track.author, inline=True)
            minutes, seconds = divmod(track.length // 1000, 60)
            embed.add_field(name="⏱️ Длительность", value=f"{minutes:02d}:{seconds:02d}", inline=True)
            
            loop_status = ["Выкл", "🔂 Трек", "🔁 Очередь"][self.loop_mode]
            embed.add_field(name="🔄 Повтор", value=loop_status, inline=True)
            
            # Добавили статус Автопилота в интерфейс
            ap_status = "Вкл 🛸" if self.autopilot else "Выкл"
            embed.add_field(name="🛸 Моя Волна(может работать некорректно)", value=ap_status, inline=True)

            if track.artwork_url:
                embed.set_thumbnail(url=track.artwork_url)

        view = MusicPlayerView(self)
        if self.message:
            try:
                await self.message.edit(embed=embed, view=view)
                return
            except: pass
        
        if self.text_channel:
            self.message = await self.text_channel.send(embed=embed, view=view)

    async def teardown(self):
        self.cancel_timeout()
        await self.redis.delete(self.queue_key)
        await self.redis.delete(self.history_key)
        if self.message:
            try: await self.message.delete()
            except: pass
        try: await self.destroy() 
        except: pass