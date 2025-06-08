from sqlalchemy import Column, Integer, String, Boolean, Date, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

class Holiday(Base):
    __tablename__ = "holidays"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    date = Column(Date, index=True)
    country = Column(String, index=True)
    state = Column(String, nullable=True, index=True)
    federal = Column(Boolean, default=False)
    notes = Column(String, nullable=True)
    is_custom = Column(Boolean, default=False)
    owner_id = Column(Integer, ForeignKey("users.id"))

    # Связь с пользователем, который добавил/изменил праздник (опционально)
    owner = relationship("User")