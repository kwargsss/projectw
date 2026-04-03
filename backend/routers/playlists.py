import json
import asyncio

from sqlalchemy import delete
from models import Playlist, PlaylistTrack
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