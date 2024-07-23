from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base

class Database(Base):
    __tablename__ = "databases"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    db_type = Column(String, nullable=False)
    db_name = Column(String, nullable=False)
    db_instance_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    backup_config = Column(String, nullable=True)

    user = relationship("User", back_populates="databases")