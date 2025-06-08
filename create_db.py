import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def create_database():
    # Подключаемся к postgres для создания новой базы данных
    engine = create_async_engine('postgresql+asyncpg://denis:123@localhost:5432/postgres')
    
    async with engine.connect() as conn:
        # Отключаем новые подключения к базе данных
        await conn.execute(text("COMMIT"))
        await conn.execute(text("DROP DATABASE IF EXISTS holydays_db"))
        await conn.execute(text("CREATE DATABASE holydays_db"))
        print("База данных holydays_db успешно создана")

if __name__ == "__main__":
    asyncio.run(create_database()) 