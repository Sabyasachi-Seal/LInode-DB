from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base
from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

Base: DeclarativeMeta = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)

class UserToDatabases(Base):
    __tablename__ = "user_to_databases"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    db_type = Column(String, nullable=False)
    db_name = Column(String, nullable=False)
    db_instance_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    backup_config = Column(String, nullable=True)

    user = relationship("User", back_populates="databases")

User.databases = relationship("UserToDatabases", order_by=UserToDatabases.id, back_populates="user")