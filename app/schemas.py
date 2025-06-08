from datetime import date as datetime_date
from typing import List, Optional, Union

from pydantic import BaseModel, Field

# User Schemas
class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    id: int
    hashed_password: str
    is_active: bool

    class Config:
        from_attributes = True # Или orm_mode = True для Pydantic v1

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# Holiday Schemas
class HolidayBase(BaseModel):
    name: str = Field(min_length=1)
    date: datetime_date
    country: str = Field(min_length=2, max_length=2) # Например, "US"
    state: Optional[str] = Field(None, min_length=2, max_length=2) # Например, "CA"
    federal: Optional[bool] = False
    notes: Optional[str] = None

class HolidayCreate(HolidayBase):
    pass

class HolidayUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    date: Optional[datetime_date] = None
    country: Optional[str] = Field(None, min_length=2, max_length=2)
    state: Optional[str] = Field(None, min_length=2, max_length=2)
    federal: Optional[bool] = None
    notes: Optional[str] = None

class HolidayInDB(HolidayBase):
    id: int
    owner_id: Optional[int] = None
    is_custom: Optional[bool] = False # Флаг для праздников, добавленных пользователем

    class Config:
        from_attributes = True # Или orm_mode = True для Pydantic v1