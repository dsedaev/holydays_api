from datetime import date
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy import select, and_
from app.models import Holiday

class HolidayFilter(BaseModel):
    name: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    federal: Optional[bool] = None
    is_custom: Optional[bool] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    states: Optional[List[str]] = None
    page: int = 1
    per_page: int = 10
    order_by: List[str] = ["id"]

async def apply_filters(query, filters: HolidayFilter):
    conditions = []

    if filters.start_date:
        conditions.append(Holiday.date >= filters.start_date)
    if filters.end_date:
        conditions.append(Holiday.date <= filters.end_date)

    if filters.name:
        conditions.append(Holiday.name.ilike(f"%{filters.name}%"))

    if filters.is_custom is not None:
        conditions.append(Holiday.is_custom == filters.is_custom)

    if filters.country:
        conditions.append(Holiday.country == filters.country)

    if filters.state:
        conditions.append(Holiday.state == filters.state)

    if filters.federal is not None:
        conditions.append(Holiday.federal == filters.federal)

    if filters.states:
        conditions.append(Holiday.state.in_(filters.states))

    if conditions:
        query = query.filter(and_(*conditions))

    for sort_field in filters.order_by:
        desc = False
        if sort_field.startswith("-"):
            desc = True
            sort_field = sort_field[1:]
        if hasattr(Holiday, sort_field):
            field = getattr(Holiday, sort_field)
            if desc:
                field = field.desc()
            query = query.order_by(field)

    return query 