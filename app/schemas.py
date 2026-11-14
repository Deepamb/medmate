from datetime import date, time
from typing import Literal

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=255)
    password: str = Field(min_length=8, max_length=72)
    timezone: str = "Asia/Kolkata"
    telegram_chat_id: str | None = None


class UserUpdate(BaseModel):
    timezone: str | None = None
    telegram_chat_id: str | None = None


class MedicineIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    dosage: str = Field(min_length=1, max_length=50)
    expiry_date: date
    quantity_left: int = Field(ge=0, default=0)


class ScheduleIn(BaseModel):
    time_of_day: time
    start_date: date
    end_date: date


class DoseUpdate(BaseModel):
    status: Literal["taken", "skipped"]
    
class CaregiverIn(BaseModel):
    email: str