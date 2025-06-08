from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

# Создаем асинхронный движок SQLAlchemy
engine = create_async_engine(settings.DATABASE_URL)

# Создаем фабрику асинхронных сессий
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Базовый класс для декларативных моделей
Base = declarative_base()

# Зависимость для получения асинхронной сессии БД
async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()