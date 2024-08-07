from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID
from app.constants.enums import DatabaseType, InstanceType, Region, BackupSchedule
from typing import Dict, Any


class DatabaseRequest(BaseModel):
    user_id: str
    db_name: str = Field(..., min_length=3, max_length=36)
    db_type: DatabaseType  # "mysql", "postgresql", or "mongodb"
    new_user: str
    new_user_password: str
    instance_type: InstanceType  # Type of Linode instance
    region: Region  # Linode region
    backup_schedule: Optional[BackupSchedule] = None  # Backup schedule


class DatabaseBackupRequest(BaseModel):
    user_id: str
    database_id: str
    hour_of_day: int
    day_of_week: Optional[int] = None  # Optional, only present for for weekly frequency
    day_of_month: Optional[int] = (
        None  # Optional, for only present for monthly frequency
    )
    frequency: BackupSchedule


class DatabaseUpdateRequest(BaseModel):
    database_id: str
    database_name: Optional[str] = None
    instance_type: Optional[str] = None


class UserBase(BaseModel):
    email: EmailStr
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False


class UserCreate(UserBase):
    password: str


class UserUpdate(UserBase):
    password: Optional[str] = None


class UserDB(UserBase):
    id: UUID
    hashed_password: str

    class Config:
        orm_mode = True


class DatabaseBackupDeleteRequest(BaseModel):
    backup_id: str


class FirewallRequest(BaseModel):
    label: str
    rules: Dict[str, Any]


class FirewallUpdateRequest(BaseModel):
    label: str
    rules: Dict[str, Any] = None
