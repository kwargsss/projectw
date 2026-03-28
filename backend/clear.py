import asyncio
import redis.asyncio as redis

from config import Config

async def clear_redis():
    r = redis.from_url(Config.REDIS_URL, decode_responses=True)
    await r.flushdb()
    print("Redis успешно очищен.")
    await r.close()

if __name__ == "__main__":
    asyncio.run(clear_redis())