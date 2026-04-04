from sqlalchemy import Column, String, Integer, BigInteger, DateTime, ForeignKey, UniqueConstraint, Boolean
from sqlalchemy.orm import relationship
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

class Playlist(Base):
    __tablename__ = "playlists"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    owner_id = Column(BigInteger, nullable=False, index=True) 
    playlist_type = Column(String(20), default="personal", nullable=False) 
    created_at = Column(DateTime, default=datetime.utcnow)
    tracks = relationship("PlaylistTrack", back_populates="playlist", cascade="all, delete-orphan")


class PlaylistTrack(Base):
    __tablename__ = "playlist_tracks"

    id = Column(Integer, primary_key=True, index=True)
    playlist_id = Column(Integer, ForeignKey("playlists.id", ondelete="CASCADE"), nullable=False)
    position = Column(Integer, nullable=False) 
    track_title = Column(String(255), nullable=False)
    track_url = Column(String(1024), nullable=False)
    source = Column(String(50), nullable=True)
    playlist = relationship("Playlist", back_populates="tracks")

class MusicStat(Base):
    __tablename__ = 'music_stats'

    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(BigInteger, nullable=False, index=True)
    entity_type = Column(String(10), nullable=False)
    track_name = Column(String(255), nullable=False)
    play_count = Column(Integer, default=0)

    __table_args__ = (
        UniqueConstraint('entity_id', 'entity_type', 'track_name', name='_entity_track_uc'),
    )

class PrivateVoiceConfig(Base):
    __tablename__ = 'private_voice_configs'

    guild_id = Column(BigInteger, primary_key=True, index=True)
    is_enabled = Column(Boolean, default=False)
    template = Column(String(100), default="🎧 Канал {user}")
    default_limit = Column(Integer, default=0)
    default_bitrate = Column(Integer, default=64000)