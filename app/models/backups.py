# app/models/backup_schedule.py
from sqlalchemy import (
    Column,
    String,
    ForeignKey,
    DateTime,
    Integer,
    Enum as SQLAlchemyEnum,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base
from app.constants.enums import BackupStatus, BackupSchedule


class BackupSchedule(Base):
    __tablename__ = "backup_schedules"

    id = Column(String(64), primary_key=True, index=True)
    database_id = Column(
        String(64), ForeignKey("databases.id", ondelete="CASCADE"), nullable=False
    )
    hour_of_day = Column(
        Integer, nullable=False
    )  # Time of day when the backup should run
    day_of_week = Column(
        Integer, nullable=True
    )  # Day of the week for weekly backups (0=Sunday, 6=Saturday)
    day_of_month = Column(
        Integer, nullable=True
    )  # Day of the month for monthly backups (1-28)
    frequency = Column(
        SQLAlchemyEnum(BackupSchedule), nullable=False
    )  # Enum: Daily, Weekly, Monthly
    status = Column(
        SQLAlchemyEnum(BackupStatus), nullable=False, default=BackupStatus.SCHEDULED
    )
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    database = relationship("Database", back_populates="backup_schedules")
