from datetime import date
from typing import Optional, List
from pydantic import BaseModel, Field

# User Schemas
class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    from_attributes = True

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# Holiday Schemas
class HolidayBase(BaseModel):
    name: str
    date: date
    country: str = Field(min_length=2, max_length=2)
    state: Optional[str] = Field(None, min_length=2, max_length=2)
    federal: Optional[bool] = False
    notes: Optional[str] = None

class HolidayCreate(HolidayBase):
    pass

class HolidayUpdate(HolidayBase):
    name: Optional[str] = None
    date: Optional[date] = None
    country: Optional[str] = None
    state: Optional[str] = None
    federal: Optional[bool] = None
    notes: Optional[str] = None
    is_custom: Optional[bool] = False

class Holiday(HolidayBase):
    id: int
    owner_id: Optional[int] = None
    from_attributes = True