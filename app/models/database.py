from sqlalchemy import Column, String, ForeignKey, DateTime, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base
from app.constants.enums import DatabaseType, InstanceType, Region, BackupSchedule

class Database(Base):
    __tablename__ = "databases"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    db_type = Column(SQLAlchemyEnum(DatabaseType), nullable=False)
    db_name = Column(String, nullable=False)
    db_instance_id = Column(String, nullable=False)
    instance_type = Column(SQLAlchemyEnum(InstanceType), nullable=False)
    region = Column(SQLAlchemyEnum(Region), nullable=False)
    backup_schedule = Column(SQLAlchemyEnum(BackupSchedule), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="databases")