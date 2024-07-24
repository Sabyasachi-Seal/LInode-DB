# app/models/backup_schedule.py
from sqlalchemy import Column, String, ForeignKey, DateTime, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base
from app.constants.enums import BackupStatus, BackupSchedule

class BackupSchedule(Base):
    __tablename__ = "backup_schedules"

    id = Column(String(36), primary_key=True, index=True)  # Assuming UUID as string
    database_id = Column(String(36), ForeignKey('databases.id'), nullable=False)
    schedule_time = Column(DateTime, nullable=False)
    frequency = Column(SQLAlchemyEnum(BackupSchedule), nullable=False)
    status = Column(SQLAlchemyEnum(BackupStatus), nullable=False, default=BackupStatus.SCHEDULED)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    database = relationship("Database", back_populates="backup_schedules")