# app/models/__init__.py
from app.models.user import User
from app.models.database import Database
from app.models.backups import BackupSchedule
# Ensure all models are imported so they are registered with Base.metadata