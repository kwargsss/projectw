import json
import asyncio

from fastapi import APIRouter, Body
from sqlalchemy import delete
from models import Playlist, PlaylistTrack, MusicStat
from database import redis_client, AsyncSessionLocal
from core.logger import setup_logger
from config import Config

logger = setup_logger("backend", Config.TG_BOT_TOKEN, Config.TG_CHAT_ID)
router = APIRouter(prefix="/api/music", tags=["Music"])

@router.get("/top/user/{user_id}")
async def get_user_top_music(user_id: int):
    key = f"music_top:user:{user_id}"
    top_tracks = await redis_client.zrevrange(key, 0, 49, withscores=True)
    result = [{"rank": i, "track_name": t.decode('utf-8') if isinstance(t, bytes) else t, "play_count": int(s)} for i, (t, s) in enumerate(top_tracks, 1)]
    return {"status": "ok", "data": result}

@router.get("/top/guild/{guild_id}")
async def get_guild_top_music(guild_id: int):
    key = f"music_top:guild:{guild_id}"
    top_tracks = await redis_client.zrevrange(key, 0, 49, withscores=True)
    result = [{"rank": i, "track_name": t.decode('utf-8') if isinstance(t, bytes) else t, "play_count": int(s)} for i, (t, s) in enumerate(top_tracks, 1)]
    return {"status": "ok", "data": result}

@router.get("/playlists/{user_id}")
async def get_playlists(user_id: int):
    playlists_raw = await redis_client.smembers(f"user_playlists:{user_id}")
    result = []
    for pl in playlists_raw:
        pl_name = pl.decode('utf-8') if isinstance(pl, bytes) else pl
        tracks_raw = await redis_client.lrange(f"playlist_tracks:{user_id}:{pl_name}", 0, -1)
        tracks = [json.loads(t.decode('utf-8') if isinstance(t, bytes) else t) for t in tracks_raw]
        result.append({"name": pl_name, "tracks": tracks})
    return {"status": "ok", "data": result}

@router.post("/playlists/{user_id}")
async def create_playlist(user_id: int, name: str = Body(..., embed=True)):
    key = f"user_playlists:{user_id}"
    if await redis_client.scard(key) >= 2:
        return {"status": "error", "message": "Лимит: максимум 2 плейлиста"}
    if await redis_client.sismember(key, name):
        return {"status": "error", "message": "Плейлист уже существует"}
    await redis_client.sadd(key, name)
    return {"status": "ok"}

@router.delete("/playlists/{user_id}/{name}")
async def delete_playlist(user_id: int, name: str):
    await redis_client.srem(f"user_playlists:{user_id}", name)
    await redis_client.delete(f"playlist_tracks:{user_id}:{name}")
    return {"status": "ok"}

@router.post("/playlists/{user_id}/{name}/tracks")
async def add_track_to_playlist(user_id: int, name: str, query: str = Body(..., embed=True)):
    if await redis_client.llen(f"playlist_tracks:{user_id}:{name}") >= 50:
        return {"status": "error", "message": "Лимит: максимум 50 треков"}
    
    payload = json.dumps({"action": "add_track", "user_id": user_id, "playlist": name, "query": query})
    await redis_client.publish("music_web_controls", payload)
    return {"status": "ok"}

@router.delete("/playlists/{user_id}/{name}/tracks/{index}")
async def delete_track_from_playlist(user_id: int, name: str, index: int):
    key = f"playlist_tracks:{user_id}:{name}"
    tracks = await redis_client.lrange(key, 0, -1)
    if 0 <= index < len(tracks):
        tracks.pop(index)
        await redis_client.delete(key)
        if tracks:
            await redis_client.rpush(key, *tracks)
    return {"status": "ok"}

@router.post("/playlists/{user_id}/{name}/import")
async def import_playlist_tracks(user_id: int, name: str, url: str = Body(..., embed=True)):
    key = f"user_playlists:{user_id}"
    if not await redis_client.sismember(key, name):
        return {"status": "error", "message": "Плейлист не найден"}
    
    payload = json.dumps({
        "action": "import_playlist", 
        "user_id": user_id, 
        "playlist": name, 
        "url": url
    })
    await redis_client.publish("music_web_controls", payload)
    return {"status": "ok"}

async def playlist_sync_task():
    while True:
        await asyncio.sleep(900)
        try:
            keys = await redis_client.keys("user_playlists:*")
            if not keys: continue
            async with AsyncSessionLocal() as db:
                async with db.begin():
                    for key in keys:
                        key_str = key.decode('utf-8') if isinstance(key, bytes) else key
                        user_id = int(key_str.split(":")[1])
                        playlists = await redis_client.smembers(key)

                        await db.execute(delete(Playlist).where(Playlist.owner_id == user_id))

                        for pl_name_bytes in playlists:
                            pl_name = pl_name_bytes.decode('utf-8') if isinstance(pl_name_bytes, bytes) else pl_name_bytes
                            new_pl = Playlist(name=pl_name, owner_id=user_id)
                            db.add(new_pl)
                            await db.flush()

                            tracks_key = f"playlist_tracks:{user_id}:{pl_name}"
                            raw_tracks = await redis_client.lrange(tracks_key, 0, -1)

                            for i, track_bytes in enumerate(raw_tracks):
                                track_json = track_bytes.decode('utf-8') if isinstance(track_bytes, bytes) else track_bytes
                                data = json.loads(track_json)
                                author = data.get('author', 'Неизвестен')
                                full_title = f"{author} - {data['title']}"
                                
                                db.add(PlaylistTrack(
                                    playlist_id=new_pl.id, position=i + 1,
                                    track_title=full_title[:255], track_url=data["url"][:1024],
                                    source=data.get("source", "unknown")[:50]
                                ))
        except Exception: pass

async def stats_sync_task():
    while True:
        await asyncio.sleep(900)
        try:
            keys = await redis_client.keys("music_top:*")
            if not keys: continue
            async with AsyncSessionLocal() as db:
                async with db.begin():
                    for key in keys:
                        key_str = key.decode('utf-8') if isinstance(key, bytes) else key
                        parts = key_str.split(":")
                        if len(parts) != 3: continue
                        
                        entity_type, entity_id = parts[1], int(parts[2])
                        top_tracks = await redis_client.zrevrange(key, 0, 49, withscores=True)
                        
                        await db.execute(delete(MusicStat).where(MusicStat.entity_id == entity_id, MusicStat.entity_type == entity_type))

                        for track_data, score in top_tracks:
                            track_name = track_data.decode('utf-8') if isinstance(track_data, bytes) else track_data
                            db.add(MusicStat(entity_id=entity_id, entity_type=entity_type, track_name=track_name[:255], play_count=int(score)))
        except Exception: pass