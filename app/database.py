from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.config import settings

# Создаем асинхронный движок SQLAlchemy
engine = create_async_engine(settings.database_url, echo=True)

# Создаем фабрику асинхронных сессий
AsyncSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Базовый класс для декларативных моделей
Base = declarative_base()

# Зависимость для получения асинхронной сессии БД
async def get_db():
    db = AsyncSessionLocal()
    try:
        yield db
    finally:
        await db.close()