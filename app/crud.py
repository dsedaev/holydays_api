from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, text, and_
from sqlalchemy.orm import selectinload
from typing import List, Optional, Union
from datetime import date
import holidays

from app.models import User, Holiday
from app.schemas import UserCreate, HolidayCreate, HolidayUpdate

from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

async def get_user(db: AsyncSession, user_id: int):
    result = await db.execute(select(User).filter(User.id == user_id))
    return result.scalar_one_or_none()

async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalar_one_or_none()

async def get_users(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(User).offset(skip).limit(limit))
    return result.scalars().all()

async def create_user(db: AsyncSession, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def get_holiday(db: AsyncSession, holiday_id: int):
    result = await db.execute(select(Holiday).filter(Holiday.id == holiday_id))
    return result.scalar_one_or_none()

async def get_holidays(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(Holiday).offset(skip).limit(limit))
    return result.scalars().all()

async def get_holidays_query(db: AsyncSession):
    return select(Holiday)

async def get_count(query):
    return len((await db.execute(query)).all())

async def get_holidays_with_pagination(query, page: int, per_page: int):
    offset = (page - 1) * per_page
    result = await db.execute(query.offset(offset).limit(per_page))
    return result.scalars().all()

async def create_holiday(db: AsyncSession, holiday: HolidayCreate, user_id: int):
    db_holiday = Holiday(**holiday.dict(), owner_id=user_id, is_custom=True)
    db.add(db_holiday)
    await db.commit()
    await db.refresh(db_holiday)
    return db_holiday

async def update_holiday(db: AsyncSession, holiday_id: int, holiday: HolidayUpdate):
    db_holiday = await get_holiday(db, holiday_id)
    update_data = holiday.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_holiday, field, value)
    await db.commit()
    await db.refresh(db_holiday)
    return db_holiday

async def delete_holiday(db: AsyncSession, holiday_id: int):
    db_holiday = await get_holiday(db, holiday_id)
    await db.delete(db_holiday)
    await db.commit()

async def import_holidays_from_lib(db: AsyncSession, year: int):
    imported_count = 0

    us_federal_holidays = holidays.US(years=year)
    for date_obj, name in us_federal_holidays.items():
        existing_holiday = await db.execute(
            select(Holiday).filter(
                and_(
                    Holiday.date == date_obj,
                    Holiday.name == name,
                    Holiday.country == "US",
                    Holiday.state.is_(None)
                )
            )
        )
        if not existing_holiday.scalar_one_or_none():
            db_holiday = Holiday(
                name=name,
                date=date_obj,
                country="US",
                state=None,
                federal=True,
                is_custom=False
            )
            db.add(db_holiday)
            imported_count += 1

    for state in holidays.US_STATES:
        state_holidays = holidays.US(years=year, state=state)
        for date_obj, name in state_holidays.items():
            if date_obj in us_federal_holidays and name == us_federal_holidays[date_obj]:
                continue

            existing_holiday = await db.execute(
                select(Holiday).filter(
                    and_(
                        Holiday.date == date_obj,
                        Holiday.name == name,
                        Holiday.country == "US",
                        Holiday.state == state
                    )
                )
            )
            if not existing_holiday.scalar_one_or_none():
                db_holiday = Holiday(
                    name=name,
                    date=date_obj,
                    country="US",
                    state=state,
                    federal=False,
                    is_custom=False
                )
                db.add(db_holiday)
                imported_count += 1

    await db.commit()
    return imported_count

async def clear_holidays_table(db: AsyncSession):
    """Clear all records from the holidays table and reset the sequence."""
    await db.execute(text("DELETE FROM holidays"))
    await db.execute(text("ALTER SEQUENCE holidays_id_seq RESTART WITH 1"))
    await db.commit()