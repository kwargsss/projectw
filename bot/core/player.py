import mafic
import disnake
import asyncio
import json
import re

from config import Config
from yandex_music import ClientAsync


class CustomPlayer(mafic.Player):
    def __init__(self, client: disnake.Client, channel: disnake.VoiceChannel):
        super().__init__(client, channel)
        self.redis = self.client.redis
        self.queue_key = f"music:queue:{self.channel.id}"
        self.history_key = f"music:history:{self.channel.id}"
        
        self.loop_mode = 0 
        self.timeout_task = None 
        self.autopilot = False 
        
        ym_token = Config.YANDEX_TOKEN
        self.ym_client = ClientAsync(token=ym_token)

    async def send_ui_update(self, track: mafic.Track = None):
        payload = {
            "event": "update_ui",
            "guild_id": self.guild.id,
            "voice_channel_id": self.channel.id,
            "worker_id": self.client.worker_id,
            "loop_mode": self.loop_mode,
            "autopilot": self.autopilot,
            "is_paused": self.paused,
            "track": None
        }
        if track:
            payload["track"] = {
                "title": track.title, "author": track.author,
                "uri": track.uri, "length": track.length,
                "artwork_url": track.artwork_url
            }
        await self.redis.publish("master_events", json.dumps(payload))

    async def play_autopilot(self, finished_track: mafic.Track):
        def clean_text(text): return re.sub(r'[^a-zа-яё0-9]', '', str(text).lower())

        try:
            if not getattr(self.ym_client, 'me', None):
                try: await self.ym_client.init()
                except: pass

            track_id = None
            if finished_track.source == "yandex": track_id = finished_track.identifier
            else:
                search = await self.ym_client.search(f"{finished_track.author} {finished_track.title}", type_="track")
                if search.tracks and search.tracks.results: track_id = search.tracks.results[0].id

            if not track_id: return None
            candidates = []
            
            for fetcher in [
                lambda: self.ym_client.rotor_station_tracks(f"track:{track_id}"),
                lambda: self.ym_client.rotor_station_tracks("user:onyourwave"),
                lambda: self.ym_client.tracks_similar(track_id)
            ]:
                try:
                    res = await fetcher()
                    if hasattr(res, 'sequence'): candidates.extend([getattr(i, 'track', i) for i in res.sequence])
                    elif hasattr(res, 'similar_tracks'): candidates.extend(res.similar_tracks)
                except: pass

            if not candidates: return None

            history = await self.redis.lrange(self.history_key, 0, 40)
            history_titles = []
            for h_id in history:
                try:
                    dec = await self.node.decode_track(h_id)
                    history_titles.append(clean_text(dec.title))
                except: pass

            finished_title_clean = clean_text(finished_track.title)
            BLACKLIST = ["remix", "cover", "bass", "slowed", "reverb", "tribute", "karaoke", "караоке", "ремикс", "кавер", "sped up", "speed up", "tiktok", "mashup", "мэшап"]

            track_to_play = None
            for t in candidates:
                try:
                    if not getattr(t, 'artists', None): continue
                    title_lower = getattr(t, 'title', '').lower()
                    if any(word in title_lower for word in BLACKLIST): continue
                    clean_t_title = clean_text(title_lower)
                    if clean_t_title == finished_title_clean or clean_t_title in history_titles: continue

                    artist_name = t.artists[0].name
                    track_to_play = f"{artist_name} {t.title}"
                    break 
                except: continue

            if not track_to_play: return None

            resolved = await self.fetch_tracks(track_to_play, search_type="ymsearch")
            if resolved:
                track = resolved[0] if isinstance(resolved, list) else resolved
                await self.play(track, start_time=0)
                return track
        except: return None
        
    async def start_timeout(self, timeout_seconds: int):
        try:
            await asyncio.sleep(timeout_seconds)
            self.timeout_task = None 
            await self.teardown() 
        except asyncio.CancelledError: pass

    def cancel_timeout(self):
        if self.timeout_task and not self.timeout_task.done(): self.timeout_task.cancel()

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
        
        if self.current: await self.redis.lpush(self.queue_key, self.current.id)
            
        track = await self.node.decode_track(track_id)
        await self.play(track, start_time=0) 
        return track

    async def teardown(self):
        self.cancel_timeout()
        
        worker_id = getattr(self.client, "worker_id", None)
        if worker_id:
            await self.redis.delete(f"vc_worker:{self.channel.id}")
            await self.redis.srem(f"guild_active_workers:{self.guild.id}", worker_id)

        await self.redis.delete(self.queue_key)
        await self.redis.delete(self.history_key)
        
        await self.redis.publish("master_events", json.dumps({
            "event": "teardown", 
            "guild_id": self.guild.id,
            "voice_channel_id": self.channel.id
        }))
        
        try: await self.destroy() 
        except: pass