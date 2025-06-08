import asyncio
from sqlalchemy import text
from app.database import AsyncSessionLocal

async def reset_database():
    async with AsyncSessionLocal() as session:
        # Удаляем схему
        await session.execute(text("DROP SCHEMA public CASCADE"))
        # Создаем схему заново
        await session.execute(text("CREATE SCHEMA public"))
        # Даем права
        await session.execute(text("GRANT ALL ON SCHEMA public TO public"))
        await session.commit()
        print("База данных успешно сброшена")

if __name__ == "__main__":
    asyncio.run(reset_database()) 