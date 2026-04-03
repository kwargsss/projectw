import json
import asyncio

from sqlalchemy import delete
from models import Playlist, PlaylistTrack, MusicStat
from database import redis_client, AsyncSessionLocal
from core.logger import setup_logger
from config import Config


logger = setup_logger("backend", Config.TG_BOT_TOKEN, Config.TG_CHAT_ID)

async def playlist_sync_task():
    while True:
        await asyncio.sleep(900)
        try:
            keys = await redis_client.keys("user_playlists:*")
            if not keys:
                continue

            async with AsyncSessionLocal() as db:
                async with db.begin():
                    for key in keys:
                        user_id = int(key.split(":")[1])
                        playlists = await redis_client.smembers(key)

                        await db.execute(delete(Playlist).where(Playlist.owner_id == user_id))

                        for pl_name in playlists:
                            new_pl = Playlist(name=pl_name, owner_id=user_id)
                            db.add(new_pl)
                            await db.flush()

                            tracks_key = f"playlist_tracks:{user_id}:{pl_name}"
                            raw_tracks = await redis_client.lrange(tracks_key, 0, -1)

                            for i, track_json in enumerate(raw_tracks):
                                data = json.loads(track_json)
                                author = data.get('author', 'Неизвестен')
                                
                                full_title = f"{author} - {data['title']}"
                                
                                db.add(PlaylistTrack(
                                    playlist_id=new_pl.id,
                                    position=i + 1,
                                    track_title=full_title[:255],
                                    track_url=data["url"][:1024],
                                    source=data.get("source", "unknown")[:50]
                                ))
            logger.info(f"[MUSIC] Синхронизировано плейлистов для {len(keys)} пользователей.")
        except Exception as e:
            logger.error(f"[MUSIC] Ошибка синхронизации плейлистов: {e}")

async def stats_sync_task():
    while True:
        await asyncio.sleep(900)
        try:
            keys = await redis_client.keys("music_top:*")
            if not keys:
                continue

            async with AsyncSessionLocal() as db:
                async with db.begin():
                    for key in keys:
                        key_str = key.decode('utf-8') if isinstance(key, bytes) else key
                        parts = key_str.split(":")
                        if len(parts) != 3:
                            continue
                        
                        entity_type = parts[1]
                        entity_id = int(parts[2])

                        top_tracks = await redis_client.zrevrange(key, 0, 49, withscores=True)
                        
                        await db.execute(
                            delete(MusicStat).where(
                                MusicStat.entity_id == entity_id,
                                MusicStat.entity_type == entity_type
                            )
                        )

                        for track_data, score in top_tracks:
                            track_name = track_data.decode('utf-8') if isinstance(track_data, bytes) else track_data
                            db.add(MusicStat(
                                entity_id=entity_id,
                                entity_type=entity_type,
                                track_name=track_name[:255],
                                play_count=int(score)
                            ))

            logger.info(f"[MUSIC] Синхронизирована статистика для {len(keys)} сущностей.")
        except Exception as e:
            logger.error(f"[MUSIC] Ошибка синхронизации статистики: {e}")