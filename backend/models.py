from sqlalchemy import Column, String, BigInteger, DateTime
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(BigInteger, primary_key=True)
    username = Column(String, nullable=False)
    discriminator = Column(String, nullable=False)
    avatar_hash = Column(String, nullable=True)
    role = Column(String, default="user")
    first_login = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, default=datetime.utcnow)