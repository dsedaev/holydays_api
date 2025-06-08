from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, text
from sqlalchemy.orm import selectinload
from typing import List, Optional, Union
from datetime import date # Добавим date для import_holidays_from_lib

from app.models import User, Holiday
from app.schemas import UserCreate, HolidayCreate, HolidayUpdate

from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalars().first()

async def create_user(db: AsyncSession, user: UserCreate) -> User:
    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def get_holiday(db: AsyncSession, holiday_id: int) -> Optional[Holiday]:
    result = await db.execute(select(Holiday).filter(Holiday.id == holiday_id))
    return result.scalars().first()

async def get_holidays(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Holiday]:
    result = await db.execute(select(Holiday).offset(skip).limit(limit))
    return list(result.scalars().all())

async def create_holiday(db: AsyncSession, holiday: HolidayCreate, owner_id: Optional[int] = None) -> Holiday:
    db_holiday = Holiday(**holiday.model_dump(), owner_id=owner_id, is_custom=bool(owner_id))
    db.add(db_holiday)
    await db.commit()
    await db.refresh(db_holiday)
    return db_holiday

async def update_holiday(db: AsyncSession, holiday_id: int, holiday_update: HolidayUpdate) -> Optional[Holiday]:
    current_holiday = await db.execute(select(Holiday).filter(Holiday.id == holiday_id))
    db_holiday = current_holiday.scalars().first()

    if not db_holiday or not db_holiday.is_custom:
        return None

    update_data = holiday_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_holiday, key, value)

    await db.commit()
    await db.refresh(db_holiday)
    return db_holiday

async def delete_holiday(db: AsyncSession, holiday_id: int) -> Optional[Holiday]:
    holiday = await db.execute(select(Holiday).filter(Holiday.id == holiday_id))
    db_holiday = holiday.scalars().first()

    if not db_holiday or not db_holiday.is_custom:
        return None

    await db.delete(db_holiday)
    await db.commit()
    return db_holiday

async def import_holidays_from_lib(db: AsyncSession, year: int, country: str = "US", state: Optional[str] = None):
    import holidays
    imported_count = 0

    # Сначала импортируем чисто федеральные праздники США (если страна US и не указан штат)
    if country == "US" and state is None:
        us_federal_holidays = holidays.US(years=year) # Используем holidays.US() для федеральных
        for date_obj, name in us_federal_holidays.items():
            existing_holiday = await db.execute(
                select(Holiday).filter(
                    Holiday.date == date_obj, 
                    Holiday.name == name, 
                    Holiday.country == country,
                    Holiday.state.is_(None) # Убедимся, что это федеральный, без штата
                )
            )
            if existing_holiday.scalars().first():
                continue

            holiday_data = HolidayCreate(
                name=name,
                date=date_obj,
                country=country,
                state=None, # Федеральные праздники не имеют штата
                federal=True, # Помечаем как федеральный
                notes=None
            )
            db_holiday = Holiday(**holiday_data.model_dump(), is_custom=False)
            db.add(db_holiday)
            imported_count += 1

    # Затем импортируем другие (национальные или штат-специфичные) праздники
    other_holidays = holidays.CountryHoliday(country, state=state, years=year)
    for date_obj, name in other_holidays.items():
        # Если это федеральный праздник, который мы уже импортировали, пропускаем
        if country == "US" and state is None and holidays.US(years=year).get(date_obj) == name:
             continue # Пропускаем, чтобы избежать дубликатов с федеральными

        existing_holiday = await db.execute(
            select(Holiday).filter(
                Holiday.date == date_obj, 
                Holiday.name == name, 
                Holiday.country == country,
                Holiday.state == state
            )
        )
        if existing_holiday.scalars().first():
            continue

        holiday_data = HolidayCreate(
            name=name,
            date=date_obj,
            country=country,
            state=state,
            federal=False, # По умолчанию false для не-федеральных/штат-специфичных
            notes=None
        )
        db_holiday = Holiday(**holiday_data.model_dump(), is_custom=False)
        db.add(db_holiday)
        imported_count += 1

    await db.commit()
    return imported_count

async def clear_holidays_table(db: AsyncSession):
    """Clear all records from the holidays table and reset the sequence."""
    await db.execute(text("DELETE FROM holidays"))
    await db.execute(text("ALTER SEQUENCE holidays_id_seq RESTART WITH 1"))
    await db.commit()