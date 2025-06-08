from datetime import date, timedelta
from typing import List, Optional, Annotated

from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select, extract
import uvicorn

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, AsyncSessionLocal
from app.models import User, Holiday
from app.schemas import UserCreate, UserInDB, Token, HolidayCreate, HolidayInDB, HolidayUpdate
from app.crud import (
    get_user_by_email, create_user, verify_password,
    create_holiday, get_holidays, get_holiday,
    update_holiday, delete_holiday, import_holidays_from_lib, clear_holidays_table
)
from app.auth import create_access_token, get_current_active_user
from app.config import settings
from app.filters import HolidayFilter, apply_filters


app = FastAPI(
    title="API для управления праздничными днями",
    description="REST API сервис для управления праздничными днями в США, "
                "включая государственные, региональные и пользовательские праздники.",
    version="0.1.0",
)

ActiveSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_active_user)]

@app.on_event("startup")
async def startup_event():
    db = AsyncSessionLocal()
    try:
        current_year = date.today().year
        imported_federal = await import_holidays_from_lib(db, current_year, country="US")
        print(f"Импортировано {imported_federal} федеральных праздников США за {current_year} год.")
    except Exception as e:
        print(f"Ошибка при импорте праздников: {e}")
    finally:
        await db.close()


@app.get("/", summary="Проверка работоспособности API")
async def root():
    return {"message": "Добро пожаловать в API праздничных дней США!"}

@app.post("/register", response_model=UserInDB, summary="Регистрация нового пользователя")
async def register_user(user: UserCreate, db: ActiveSession):
    db_user = await get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email уже зарегистрирован")
    new_user = await create_user(db=db, user=user)
    return new_user

@app.post("/token", response_model=Token, summary="Получение JWT-токена авторизации")
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: ActiveSession):
    user = await get_user_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неправильный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me/", response_model=UserInDB, summary="Получение информации о текущем авторизованном пользователе")
async def read_users_me(current_user: CurrentUser):
    return current_user

@app.post("/holidays/import", status_code=status.HTTP_201_CREATED, summary="Импорт праздников из библиотеки holidays")
async def import_holidays_route(
    db: ActiveSession,
    current_user: CurrentUser,
    year: Annotated[int, Query(description="Год для импорта праздников")],
    country: Annotated[str, Query(description="Страна для импорта")] = "US",
    state: Annotated[Optional[str], Query(description="Штат для импорта (если применимо)")] = None
):
    imported_count = await import_holidays_from_lib(db, year, country, state)
    return {"message": f"Успешно импортировано {imported_count} праздников."}


@app.post("/holidays", response_model=HolidayInDB, status_code=status.HTTP_201_CREATED, summary="Добавление нового пользовательского праздника")
async def create_new_holiday(
    holiday: HolidayCreate,
    db: ActiveSession,
    current_user: CurrentUser
):
    new_holiday = await create_holiday(db=db, holiday=holiday, owner_id=current_user.id)
    return new_holiday

@app.get("/holidays", response_model=List[HolidayInDB], summary="Получение списка праздников с фильтрацией")
async def list_holidays(
    db: ActiveSession,
    holiday_filter: HolidayFilter = Depends(),
    year: Optional[int] = Query(None, description="Год для фильтрации"),
    month: Optional[int] = Query(None, description="Месяц для фильтрации"),
    states: Optional[str] = Query(None, description="Фильтр по праздникам группы штатов (например, NY,TX,FL)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=200)
):
    query = select(Holiday)
    
    # Применяем фильтры
    query = holiday_filter.filter(query)

    # Ручные фильтры для YEAR/MONTH
    if year:
        query = query.filter(extract('year', Holiday.date) == year)
    if month:
        query = query.filter(extract('month', Holiday.date) == month)
    
    # Ручная обработка 'states'
    if states:
        state_list = [s.strip().upper() for s in states.split(',')]
        query = query.filter(Holiday.state.in_(state_list))

    # Пагинация и сортировка
    query = query.offset(skip).limit(limit)
    
    # Применяем сортировку, если она указана
    if holiday_filter.order_by:
        query = holiday_filter.sort(query)

    result = await db.execute(query)
    holidays_data = result.scalars().all()
    return list(holidays_data)


@app.put("/holidays/{holiday_id}", response_model=HolidayInDB, summary="Редактирование пользовательского праздника")
async def update_existing_holiday(
    holiday_id: int,
    holiday_update: HolidayUpdate,
    db: ActiveSession,
    current_user: CurrentUser
):
    updated_holiday = await update_holiday(db, holiday_id, holiday_update)
    if not updated_holiday:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Праздник не найден или не является пользовательским")
    
    if updated_holiday.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет прав на редактирование этого праздника")
        
    return updated_holiday

@app.delete("/holidays/{holiday_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Удаление пользовательского праздника")
async def delete_existing_holiday(
    holiday_id: int,
    db: ActiveSession,
    current_user: CurrentUser
):
    holiday_to_delete = await get_holiday(db, holiday_id)
    if not holiday_to_delete or not holiday_to_delete.is_custom:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Праздник не найден или не является пользовательским")
    
    if holiday_to_delete.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет прав на удаление этого праздника")

    await delete_holiday(db, holiday_id)
    return {"message": "Праздник успешно удален"}

@app.delete("/api/holidays/clear", response_model=dict)
async def clear_holidays(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Clear all records from the holidays table. Only for admin users."""
    if not current_user.email == "admin@example.com":  # Простая проверка на админа
        raise HTTPException(
            status_code=403,
            detail="Only admin users can clear the holidays table"
        )
    await clear_holidays_table(db)
    return {"message": "All holidays have been cleared successfully"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)