import asyncio
from redis.asyncio import Redis

async def clear_all():
    REDIS_URL = "redis://default:qHsXxP1PU5SOiEqWCYJeqKYUOxINe0PD@redis-19263.crce218.eu-central-1-1.ec2.cloud.redislabs.com:19263"
    
    print("Подключение к облачному Redis...")
    client = Redis.from_url(REDIS_URL)

    await client.flushall()
    print("✅ Облачная база данных Redis успешно и полностью очищена!")
    
    await client.aclose()

if __name__ == "__main__":
    asyncio.run(clear_all())