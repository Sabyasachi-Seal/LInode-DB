from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
from app.models import Database, BackupSchedule
from app.models.requests import DatabaseRequest, DatabaseBackupRequest, DatabaseUpdateRequest
# from app.auth.auth import auth_backend, fastapi_users, current_active_user
from app.utils.linode import create_linode_instance, deploy_backup_script, update_linode_instance, delete_linode_instance
from app.utils.db import get_db, convert_schedule_to_cron, validate_backup_schedule_inputs
from app.models.requests import UserCreate, UserUpdate, UserDB
from app.constants.enums import BackupStatus
from datetime import datetime
from sqlalchemy.future import select
from sqlalchemy.exc import NoResultFound
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# # Include the FastAPI Users routes
# app.include_router(
#     fastapi_users.get_auth_router(auth_backend),
#     prefix="/auth/jwt",
#     tags=["auth"],
# )
# app.include_router(
#     fastapi_users.get_register_router(user_create_schema=UserCreate, user_schema=UserDB),
#     prefix="/auth",
#     tags=["auth"],
# )
# app.include_router(
#     fastapi_users.get_users_router(user_update_schema=UserUpdate, user_schema=UserDB),
#     prefix="/users",
#     tags=["users"],
# )

@app.post("/create_database/")
async def create_database(db_request: DatabaseRequest, session: AsyncSession = Depends(get_db)):
    try:
        label = f"{db_request.db_type}-{str(uuid4())}"
        new_pass = str(uuid4())
        # Create the Linode instance
        instance = create_linode_instance(
            label=label,
            db_type=db_request.db_type,
            db_root_password=new_pass,
            new_user=db_request.new_user,
            new_user_password=db_request.new_user_password,
            instance_type=db_request.instance_type,
            region=db_request.region
        )

        # Store the database information in the Database table
        db_instance = Database(
            id=str(uuid4()),
            user_id="1",  # Use a dummy user ID for now
            db_type=db_request.db_type,
            db_name=label,
            db_instance_id=str(instance.id),
            instance_type=db_request.instance_type,
            region=db_request.region,
            db_root_password=new_pass,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        session.add(db_instance)
        await session.commit()

        return {"message": "Database instance created successfully", "instance_id": db_instance.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating database instance: {str(e)}")
    
@app.get("/databases/")
async def list_databases(session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(Database))
    databases = result.scalars().all()
    return databases

@app.get("/databases/{database_id}")
async def get_database(database_id: str, session: AsyncSession = Depends(get_db)):
    try:
        result = await session.execute(select(Database).where(Database.id == database_id))
        database = result.scalar_one()
        return database
    except NoResultFound:
        raise HTTPException(status_code=400, detail="Database not found")

@app.delete("/databases/{database_id}")
async def delete_database(database_id: str, session: AsyncSession = Depends(get_db)):
    try:
        result = await session.execute(select(Database).where(Database.id == database_id))
        database = result.scalar_one()
        delete_linode_instance(database.db_instance_id)
        await session.delete(database)
        await session.commit()
        return {"message": "Database deleted successfully"}
    except NoResultFound:
        raise HTTPException(status_code=400, detail="Database not found")

@app.put("/databases/")
async def update_database(db_update: DatabaseUpdateRequest, session: AsyncSession = Depends(get_db)):
    try:
        result = await session.execute(select(Database).where(Database.id == db_update.database_id))
        database = result.scalar_one()

        # update the instance type in linode
        update_linode_instance(
            instance_id=database.db_instance_id,
            instance_type=db_update.instance_type,
            region=database.region
        )

        # Update fields
        database.db_name = db_update.db_name or database.db_name
        database.instance_type = db_update.instance_type or database.instance_type
        database.region = db_update.region or database.region
        database.updated_at = datetime.utcnow()

        session.add(database)
        await session.commit()
        return {"message": "Database updated successfully"}
    except NoResultFound:
        raise HTTPException(status_code=400, detail="Database not found")

@app.post("/schedule_backup/")
async def schedule_backup(
    backup_request: DatabaseBackupRequest,
    session: AsyncSession = Depends(get_db)
):

    try:
        # get the request data
        database_id = backup_request.database_id
        backup_hour_of_day = backup_request.hour_of_day
        backup_day_of_week = backup_request.day_of_week
        backup_day_of_month = backup_request.day_of_month
        backup_frequency = backup_request.frequency


        if not validate_backup_schedule_inputs(
            hour_of_day=backup_hour_of_day,
            day_of_week=backup_day_of_week,
            day_of_month=backup_day_of_month,
            frequency=backup_frequency
        ):
            raise HTTPException(status_code=400, detail="Invalid backup schedule parameters.")

        # Generate cron expression (assuming function is implemented)
        cron_expression = convert_schedule_to_cron(
            hour_of_day=backup_hour_of_day,
            day_of_week=backup_day_of_week,
            day_of_month=backup_day_of_month,
            frequency=backup_frequency
        )

        # Get the database instance
        database = await session.get(Database, database_id)

        status = deploy_backup_script(
            instance_id=database.db_instance_id,
            cron_schedule=cron_expression,
            db_type=database.db_type
            
        )

        # Create backup schedule
        new_backup_schedule = BackupSchedule(
            id=str(uuid4()),
            database_id=database_id,
            hour_of_day=backup_hour_of_day,
            day_of_week=backup_day_of_week,
            day_of_month=backup_day_of_month,
            frequency=backup_frequency,
            status=BackupStatus.SCHEDULED,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        session.add(new_backup_schedule)
        await session.commit()

        return {"message": "Backup schedule created successfully", "schedule_id": new_backup_schedule.id, "status": status}
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Error scheduling backup: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)