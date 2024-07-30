from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator
from datetime import time
from app.constants.enums import BackupSchedule, DatabaseType
from app.config import settings
import pymysql
from app.constants.contants import INSTANCE_DEFAULT_USER
from app.utils.linode import get_server_ip

DATABASE_URL = f"mysql+aiomysql://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"

engine = create_async_engine(DATABASE_URL, echo=True)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


def validate_backup_schedule_inputs(
    hour_of_day: int, day_of_week: int, day_of_month: int, frequency: BackupSchedule
):
    errors = []

    if not (0 <= hour_of_day <= 23):
        errors.append("hour_of_day must be an integer between 0 and 23.")

    # Frequency-specific validations
    if frequency == BackupSchedule.daily.value:
        if day_of_week is not None or day_of_month is not None:
            errors.append(
                "No day_of_week or day_of_month should be set for daily backups."
            )

    elif frequency == BackupSchedule.weekly.value:
        if day_of_week is None:
            errors.append("day_of_week must be set for weekly backups.")
        elif not (0 <= day_of_week <= 6):
            errors.append(
                "day_of_week must be an integer between 0 (Sunday) and 6 (Saturday)."
            )
        if day_of_month is not None:
            errors.append("day_of_month should not be set for weekly backups.")

    elif frequency == BackupSchedule.monthly.value:
        if day_of_month is None:
            errors.append("day_of_month must be set for monthly backups.")
        elif not (1 <= day_of_month <= 31):
            errors.append("day_of_month must be an integer between 1 and 31.")
        if day_of_week is not None:
            errors.append("day_of_week should not be set for monthly backups.")

    # Return validation results
    if errors:
        print(errors)
        return False
    return True


def convert_schedule_to_cron(
    hour_of_day: int, day_of_week: int, day_of_month: int, frequency: BackupSchedule
) -> str:
    """
    Converts validated backup schedule parameters into a cron expression.
    """

    minute = "0"  # NOTE: Assuming backups are scheduled at the beginning of the hour

    if frequency == BackupSchedule.daily.value:
        # Runs every day at the specified hour
        cron_expression = f"{minute} {hour_of_day} * * *"

    elif frequency == BackupSchedule.weekly.value:
        # Runs on a specific day of the week at the specified hour
        cron_expression = f"{minute} {hour_of_day} * * {day_of_week}"

    elif frequency == BackupSchedule.monthly.value:
        # Runs on a specific day of the month at the specified hour
        cron_expression = f"{minute} {hour_of_day} {day_of_month} * *"

    else:
        raise ValueError("Unsupported frequency type")

    return cron_expression


def check_connection_to_database(
    db_type: DatabaseType,
    instance_id: str,
    password: str,
    user: str = INSTANCE_DEFAULT_USER,
):
    """
    Check if the application can connect to the database
    """

    # Get the database instance details
    server_ip = get_server_ip(instance_id)

    if db_type == DatabaseType.mysql.value:
        try:

            connection = pymysql.connect(
                host=server_ip,
                port=3306,
                user=user,
                password=password,
                connect_timeout=30,
            )
            connection.close()
            return True
        except Exception as e:
            print(f"Error connecting to the database: {str(e)}")
            return False
    else:
        raise ValueError("Unsupported database type", db_type)
