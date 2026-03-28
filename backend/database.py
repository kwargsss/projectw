import redis.asyncio as redis

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
from config import Config

engine = create_async_engine(
    Config.DATABASE_URL, 
    echo=False,
    poolclass=NullPool,
    connect_args={"statement_cache_size": 0, "ssl": "require"} if "postgres" in Config.DATABASE_URL else {}
)

AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

redis_client = redis.from_url(Config.REDIS_URL, decode_responses=True)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)