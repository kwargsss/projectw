from sqlalchemy import JSON, Boolean, Column, String, Integer, BigInteger, DateTime
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(BigInteger, primary_key=True)
    username = Column(String, nullable=False)
    discriminator = Column(String, nullable=False)
    avatar_hash = Column(String, nullable=True)
    role = Column(String, default="user")
    background_file = Column(String, nullable=True)
    first_login = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, default=datetime.utcnow)

class MemberStats(Base):
    __tablename__ = "member_stats"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, unique=True, nullable=False, index=True)
    xp = Column(BigInteger, default=0)
    level = Column(Integer, default=0)
    messages_count = Column(Integer, default=0)
    voice_minutes = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)