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
    name = Column(String, index=True)
    date = Column(Date, index=True)
    country = Column(String, index=True)
    state = Column(String, nullable=True, index=True) # Штат для региональных праздников
    federal = Column(Boolean, default=False) # Федеральный или нет
    notes = Column(String, nullable=True) # Дополнительные заметки
    is_custom = Column(Boolean, default=False) # Пользовательский праздник или импортированный

    # Связь с пользователем, который добавил/изменил праздник (опционально)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    owner = relationship("User")