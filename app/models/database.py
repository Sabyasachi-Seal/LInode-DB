# app/models/database.py
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
from app.constants.enums import DatabaseType, InstanceType, Region


class Database(Base):
    __tablename__ = "databases"

    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    db_type = Column(String(50), nullable=False)
    db_name = Column(String(100), nullable=False)
    db_instance_id = Column(String(100), nullable=False)
    instance_type = Column(String(50), nullable=False)
    region = Column(String(50), nullable=False)
    instance_root_password = Column(
        String(100), nullable=False
    )  # Password for the database instance
    db_root_password = Column(
        String(100), nullable=False
    )  # Root password for the database
    firewall_id = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="databases")
    backup_schedules = relationship(
        "BackupSchedule", back_populates="database", cascade="all, delete-orphan"
    )
