import disnake
import json
import mafic
import redis.exceptions
import asyncio
import traceback
import mafic

from disnake.ext import commands
from core.player import CustomPlayer


BLACKLIST_WORDS = ["remix", "cover", "bass boost", "slowed", "reverb", "tribute", "karaoke", "караоке", "ремикс", "кавер"]

async def playlist_autocomp(inter: disnake.ApplicationCommandInteraction, user_input: str):
    set_key = f"user_playlists:{inter.author.id}"
    playlists = await inter.bot.redis.smembers(set_key)
    return [pl for pl in playlists if user_input.lower() in pl.lower()][:25]

class MusicPlaylists(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.web_music_listener())

    async def web_music_listener(self):
        import redis.exceptions
        import asyncio
        import json
        import mafic

        await self.bot.wait_until_ready()
        
        while True:
            try:
                pubsub = self.bot.redis.pubsub()
                await pubsub.subscribe("music_web_controls")
                
                while True:
                    message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=60.0)
                    
                    if message and message['type'] == 'message':
                        try:
                            data_str = message['data']
                            if isinstance(data_str, bytes):
                                data_str = data_str.decode('utf-8')
                                
                            data = json.loads(data_str)
                            action = data.get("action")
                            user_id = data.get("user_id")
                            playlist = data.get("playlist")
                            tracks_key = f"playlist_tracks:{user_id}:{playlist}"

                            if action == "add_track":
                                query = data["query"]
                                if await self.bot.redis.llen(tracks_key) >= 50:
                                    continue
                                    
                                if not getattr(self.bot, 'pool', None) or not self.bot.pool.nodes:
                                    continue
                                    
                                node = self.bot.pool.nodes[0]
                                tracks, fallback_track = None, None
                                
                                if query.startswith("http://") or query.startswith("https://"):
                                    try: 
                                        tracks = await node.fetch_tracks(query, search_type="ytsearch")
                                    except: pass
                                else:
                                    for s_type in ["ymsearch", "ytsearch", "vksearch"]:
                                        try:
                                            found = await node.fetch_tracks(query, search_type=s_type)
                                            if found:
                                                if isinstance(found, mafic.Playlist):
                                                    tracks = found
                                                    break
                                                if not fallback_track: fallback_track = found[0]
                                                for t in found:
                                                    if self.is_original(t.title):
                                                        tracks = [t]
                                                        break
                                            if tracks: break
                                        except: continue
                                            
                                if not tracks and fallback_track:
                                    tracks = [fallback_track]
                                    
                                if tracks:
                                    track = tracks.tracks[0] if isinstance(tracks, mafic.Playlist) else tracks[0]
                                    track_data = {"title": track.title, "author": track.author, "url": track.uri, "source": track.source}
                                    await self.bot.redis.rpush(tracks_key, json.dumps(track_data))

                            elif action == "import_playlist":
                                url = data.get("url")
                                current_count = await self.bot.redis.llen(tracks_key)
                                available_slots = 50 - current_count
                                
                                if available_slots <= 0:
                                    continue

                                node = self.bot.pool.nodes[0]
                                try:
                                    clean_url = url.split("?")[0]
                                    result = await node.fetch_tracks(clean_url, search_type="ytsearch")
                                    
                                    if not result:
                                        continue

                                    if isinstance(result, mafic.Playlist):
                                        tracks_to_add = result.tracks
                                    elif isinstance(result, list):
                                        tracks_to_add = result
                                    else:
                                        tracks_to_add = [result]

                                    tracks_to_add = tracks_to_add[:available_slots]
                                    
                                    async with self.bot.redis.pipeline(transaction=True) as pipe:
                                        for track in tracks_to_add:
                                            t_data = {"title": track.title, "author": track.author, "url": track.uri, "source": track.source}
                                            pipe.rpush(tracks_key, json.dumps(t_data))
                                        await pipe.execute()
                                except: pass

                        except: pass
                    
                    await pubsub.ping()
                            
            except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError):
                await asyncio.sleep(5)
                
            except Exception:
                await asyncio.sleep(5)

    def is_original(self, track_title: str) -> bool:
        title_lower = track_title.lower()
        for word in BLACKLIST_WORDS:
            if word in title_lower:
                return False
        return True

    @commands.slash_command(name="плейлист", description="Управление личными плейлистами")
    async def playlist_group(self, inter):
        pass

    @playlist_group.sub_command(name="список", description="Показать все ваши плейлисты и лимиты")
    async def playlist_list(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=True)
        user_id = inter.author.id
        set_key = f"user_playlists:{user_id}"
        
        playlists = await self.bot.redis.smembers(set_key)
        if not playlists:
            return await inter.edit_original_response("📭 У вас пока нет плейлистов. Создайте первый командой: `/плейлист создать`")

        embed = disnake.Embed(title="📁 Ваши плейлисты", description=f"Лимит: {len(playlists)}/2", color=0x2b2d31)
        for pl in playlists:
            count = await self.bot.redis.llen(f"playlist_tracks:{user_id}:{pl}")
            embed.add_field(name=f"🎵 {pl}", value=f"Треков: {count}/50", inline=False)

        await inter.edit_original_response(embed=embed)

    @playlist_group.sub_command(name="создать", description="Создать новый плейлист (Максимум 2)")
    async def playlist_create(self, inter: disnake.ApplicationCommandInteraction, name: str = commands.Param(name="название")):
        await inter.response.defer(ephemeral=True)
        user_id = inter.author.id
        set_key = f"user_playlists:{user_id}"

        count = await self.bot.redis.scard(set_key)
        if count >= 2:
            return await inter.edit_original_response("❌ Вы достигли лимита! У вас уже есть 2 плейлиста.")

        exists = await self.bot.redis.sismember(set_key, name)
        if exists:
            return await inter.edit_original_response(f"❌ Плейлист с названием **{name}** уже существует!")

        await self.bot.redis.sadd(set_key, name)
        await inter.edit_original_response(f"✅ Плейлист **{name}** успешно создан!")

    @playlist_group.sub_command(name="удалить", description="Удалить плейлист целиком")
    async def playlist_delete(self, inter: disnake.ApplicationCommandInteraction, playlist: str = commands.Param(name="плейлист", autocomplete=playlist_autocomp)):
        await inter.response.defer(ephemeral=True)
        user_id = inter.author.id
        set_key = f"user_playlists:{user_id}"
        tracks_key = f"playlist_tracks:{user_id}:{playlist}"

        exists = await self.bot.redis.sismember(set_key, playlist)
        if not exists:
            return await inter.edit_original_response(f"❌ Плейлист **{playlist}** не найден.")

        await self.bot.redis.srem(set_key, playlist)
        await self.bot.redis.delete(tracks_key)
        await inter.edit_original_response(f"🗑️ Плейлист **{playlist}** полностью удален.")

    @playlist_group.sub_command(name="добавить", description="Добавить один трек в плейлист по названию")
    async def playlist_add(
        self, inter: disnake.ApplicationCommandInteraction, 
        playlist: str = commands.Param(name="плейлист", autocomplete=playlist_autocomp), 
        query: str = commands.Param(name="запрос")
    ):
        await inter.response.defer(ephemeral=True)
        user_id = inter.author.id
        set_key = f"user_playlists:{user_id}"
        tracks_key = f"playlist_tracks:{user_id}:{playlist}"

        exists = await self.bot.redis.sismember(set_key, playlist)
        if not exists:
            return await inter.edit_original_response(f"❌ Плейлист **{playlist}** не найден.")

        track_count = await self.bot.redis.llen(tracks_key)
        if track_count >= 50:
            return await inter.edit_original_response(f"❌ Плейлист **{playlist}** заполнен! (50/50 треков).")

        player = getattr(inter.guild, "voice_client", None)
        node = player if player else self.bot.pool.nodes[0]
        tracks, fallback_track = None, None

        if query.startswith("http://") or query.startswith("https://"):
            try: tracks = await node.fetch_tracks(query, search_type="ytsearch")
            except: pass
        else:
            for s_type in ["ymsearch", "ytsearch", "vksearch"]:
                try:
                    found_tracks = await node.fetch_tracks(query, search_type=s_type)
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

        if not tracks:
            return await inter.edit_original_response("❌ По вашему запросу трек не найден.")

        track = tracks.tracks[0] if isinstance(tracks, mafic.Playlist) else tracks[0]

        track_data = {"title": track.title, "author": track.author, "url": track.uri, "source": track.source}
        await self.bot.redis.rpush(tracks_key, json.dumps(track_data))

        # Изменено отображение лимита
        await inter.edit_original_response(f"✅ Трек **{track.author} - {track.title}** сохранен в **{playlist}** ({track_count + 1}/50)!")

    @playlist_group.sub_command(name="импорт", description="Импортировать плейлист из Яндекса/ВК/Spotify/YouTube по ссылке")
    async def playlist_import(
        self, inter: disnake.ApplicationCommandInteraction, 
        playlist: str = commands.Param(name="плейлист", autocomplete=playlist_autocomp),
        url: str = commands.Param(name="ссылка")
    ):
        await inter.response.defer(ephemeral=True)
        user_id = inter.author.id
        set_key = f"user_playlists:{user_id}"
        tracks_key = f"playlist_tracks:{user_id}:{playlist}"

        exists = await self.bot.redis.sismember(set_key, playlist)
        if not exists:
            return await inter.edit_original_response(f"❌ Плейлист **{playlist}** не найден.")

        current_count = await self.bot.redis.llen(tracks_key)
        # Увеличено доступное количество слотов до 50
        available_slots = 50 - current_count
        if available_slots <= 0:
            return await inter.edit_original_response(f"❌ Ваш плейлист **{playlist}** уже полностью заполнен (50/50).")

        clean_url = url.split("?")[0]
        player = getattr(inter.guild, "voice_client", None)
        node = player if player else self.bot.pool.nodes[0]
        
        try:
            result = await node.fetch_tracks(clean_url, search_type="ytsearch")
        except Exception as e:
            return await inter.edit_original_response(f"❌ Ошибка площадки. Убедитесь, что плейлист публичный.\n*(Техническая ошибка: {e})*")

        if not result:
            return await inter.edit_original_response("❌ Плейлист не найден. Возможно, он скрыт настройками приватности площадки.")

        if isinstance(result, mafic.Playlist):
            tracks_to_add = result.tracks
            source_name = result.name
        elif isinstance(result, list):
            tracks_to_add = result
            source_name = "Сборник треков"
        else:
            tracks_to_add = [result]
            source_name = "Одиночный трек"

        total_found = len(tracks_to_add)
        tracks_to_add = tracks_to_add[:available_slots]

        async with self.bot.redis.pipeline(transaction=True) as pipe:
            for track in tracks_to_add:
                track_data = {"title": track.title, "author": track.author, "url": track.uri, "source": track.source}
                pipe.rpush(tracks_key, json.dumps(track_data))
            await pipe.execute()

        msg = f"✅ Успешно импортировано **{len(tracks_to_add)}** треков из **{source_name}** в плейлист **{playlist}**."
        if total_found > available_slots:
            msg += f"\n⚠️ Плейлист площадки содержит больше треков ({total_found}), но был достигнут лимит, добавлены только первые {len(tracks_to_add)}."

        await inter.edit_original_response(msg)

    @playlist_group.sub_command(name="треки", description="Посмотреть список треков в плейлисте")
    async def playlist_tracks_list(self, inter: disnake.ApplicationCommandInteraction, playlist: str = commands.Param(name="плейлист", autocomplete=playlist_autocomp)):
        await inter.response.defer(ephemeral=True)
        user_id = inter.author.id
        set_key = f"user_playlists:{user_id}"
        tracks_key = f"playlist_tracks:{user_id}:{playlist}"

        exists = await self.bot.redis.sismember(set_key, playlist)
        if not exists: return await inter.edit_original_response(f"❌ Плейлист **{playlist}** не найден.")

        tracks = await self.bot.redis.lrange(tracks_key, 0, -1)
        embed = disnake.Embed(title=f"🎵 Треки: {playlist}", color=0x2b2d31)
        
        if not tracks:
            embed.description = "📭 Плейлист пуст."
            return await inter.edit_original_response(embed=embed)

        desc = ""
        for i, t in enumerate(tracks):
            d = json.loads(t)
            author = d.get('author', 'Неизвестен')
            desc += f"**{i+1}.** {author} — {d['title']}\n"
            
        embed.description = desc
        # Изменено отображение общего количества
        embed.set_footer(text=f"Всего треков: {len(tracks)}/50")
        await inter.edit_original_response(embed=embed)

    @playlist_group.sub_command(name="играть", description="Включить сохраненный плейлист")
    async def playlist_play(self, inter: disnake.ApplicationCommandInteraction, playlist: str = commands.Param(name="плейлист", autocomplete=playlist_autocomp)):
        await inter.response.defer(ephemeral=True)
        user_id = inter.author.id
        set_key = f"user_playlists:{user_id}"
        tracks_key = f"playlist_tracks:{user_id}:{playlist}"

        if not inter.author.voice or not inter.author.voice.channel:
            return await inter.edit_original_response("❌ Ты должен находиться в голосовом канале!")

        exists = await self.bot.redis.sismember(set_key, playlist)
        if not exists: return await inter.edit_original_response(f"❌ Плейлист **{playlist}** не найден.")

        raw_tracks = await self.bot.redis.lrange(tracks_key, 0, -1)
        if not raw_tracks: return await inter.edit_original_response(f"❌ Плейлист **{playlist}** пуст.")

        if not inter.guild.voice_client:
            player = await inter.author.voice.channel.connect(cls=CustomPlayer)
            await inter.guild.change_voice_state(channel=inter.author.voice.channel, self_deaf=True)
        else:
            player = inter.guild.voice_client
            if player.channel != inter.author.voice.channel:
                return await inter.edit_original_response(f"❌ Я уже занят в канале {player.channel.mention}!")

        player.text_channel = inter.channel
        player.cancel_timeout()

        await inter.edit_original_response(f"🔄 Загружаю {len(raw_tracks)} треков из **{playlist}**... Ожидайте.")

        loaded_count = 0
        for track_json in raw_tracks:
            try:
                data = json.loads(track_json)
                resolved_tracks = await player.fetch_tracks(data["url"], search_type="ytsearch")
                if resolved_tracks:
                    track = resolved_tracks[0] if isinstance(resolved_tracks, list) else resolved_tracks
                    await player.add_to_queue(track)
                    loaded_count += 1
            except: pass 

        if loaded_count == 0: return await inter.edit_original_response("❌ Не удалось загрузить ни один трек.")

        if not player.current:
            track = await player.play_next()
            await player.update_player_ui(track)

        await inter.edit_original_response(f"▶️ Плейлист **{playlist}** включен! В очередь добавлено {loaded_count} треков.")

def setup(bot):
    bot.add_cog(MusicPlaylists(bot))