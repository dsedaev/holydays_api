from datetime import date
from typing import Optional, List, Annotated

from fastapi_filter.contrib.sqlalchemy import Filter
from pydantic import BeforeValidator
from typing_extensions import Annotated
from app.models import Holiday


def parse_date(value) -> Optional[date]:
    if not value:
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный формат даты. Используйте формат YYYY-MM-DD"
        )


DateField = Annotated[Optional[date], BeforeValidator(parse_date)]


class HolidayFilter(Filter):
    id: Optional[int] = None
    name: Optional[str] = None
    date: DateField = None
    country: Optional[str] = None
    state: Optional[str] = None
    federal: Optional[bool] = None
    notes: Optional[str] = None
    owner_id: Optional[int] = None
    is_custom: Optional[bool] = None

    # Фильтрация по диапазону дат
    date__gte: DateField = None
    date__lte: DateField = None

    # Поиск по названию (частичное совпадение, регистронезависимый)
    name__ilike: Optional[str] = None

    # Фильтр для пользовательских праздников
    is_custom__eq: Optional[bool] = None

    order_by: List[str] = ["id"]  # Пример сортировки

    class Constants(Filter.Constants):
        model = Holiday

    def filter_date(self, query, value):
        if not value:
            return query
        try:
            # Преобразуем строку в объект date
            date_value = date.fromisoformat(value)
            return query.filter(self.Constants.model.date == date_value)
        except ValueError:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Неверный формат даты. Используйте формат YYYY-MM-DD"
            )

    def filter_date__gte(self, query, value):
        if not value:
            return query
        try:
            # Преобразуем строку в объект date
            date_value = date.fromisoformat(value)
            return query.filter(self.Constants.model.date >= date_value)
        except ValueError:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Неверный формат даты. Используйте формат YYYY-MM-DD"
            )

    def filter_date__lte(self, query, value):
        if not value:
            return query
        try:
            # Преобразуем строку в объект date
            date_value = date.fromisoformat(value)
            return query.filter(self.Constants.model.date <= date_value)
        except ValueError:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Неверный формат даты. Используйте формат YYYY-MM-DD"
            ) 