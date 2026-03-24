import os
import redis.asyncio as redis

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, String, BigInteger, DateTime
from sqlalchemy.pool import NullPool
from datetime import datetime
from dotenv import load_dotenv


load_dotenv()

raw_db_url = os.getenv("DATABASE_URL")
if "?sslmode=require" in raw_db_url:
    DB_URL = raw_db_url.replace("?sslmode=require", "")
else:
    DB_URL = raw_db_url

REDIS_URL = os.getenv("REDIS_URL")

engine = create_async_engine(
    DB_URL, 
    echo=False,
    poolclass=NullPool,
    connect_args={
        "statement_cache_size": 0,
        "ssl": "require"
    }
)

AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(BigInteger, primary_key=True)
    username = Column(String, nullable=False)
    discriminator = Column(String, nullable=False)
    avatar_hash = Column(String, nullable=True)
    first_login = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, default=datetime.utcnow)

redis_client = redis.from_url(REDIS_URL, decode_responses=True)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)