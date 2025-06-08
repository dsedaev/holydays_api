import asyncio
from sqlalchemy import text
from app.database import engine

async def create_db():
    async with engine.begin() as conn:
        await conn.execute(text('UPDATE pg_database SET datallowconn = false WHERE datname = current_database();'))
        await conn.execute(text('SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = current_database() AND pid <> pg_backend_pid();'))
        await conn.execute(text('DROP DATABASE IF EXISTS holydays_db;'))
        await conn.execute(text('CREATE DATABASE holydays_db;'))

if __name__ == "__main__":
    asyncio.run(create_db()) 