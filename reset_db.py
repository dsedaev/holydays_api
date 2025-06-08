import asyncio
from sqlalchemy import text
from app.database import engine

async def reset_db():
    async with engine.begin() as conn:
        await conn.execute(text('DROP SCHEMA public CASCADE;'))
        await conn.execute(text('CREATE SCHEMA public;'))
        await conn.execute(text('GRANT ALL ON SCHEMA public TO "user";'))

if __name__ == "__main__":
    asyncio.run(reset_db()) 