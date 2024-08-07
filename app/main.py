from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
from app.models import Database, BackupSchedule
from app.models.requests import (
    DatabaseRequest,
    DatabaseBackupRequest,
    DatabaseUpdateRequest,
    DatabaseBackupDeleteRequest,
    FirewallRequest,
    FirewallUpdateRequest,
)

# from app.auth.auth import auth_backend, fastapi_users, current_active_user
from app.utils.linode import (
    create_linode_instance,
    deploy_backup_script,
    update_linode_instance,
    delete_linode_instance,
    get_unique_instance_name,
    get_instance_name_from_label,
    get_linode_stats,
    get_instance_status,
    get_backups,
    get_linode_instance_details,
    delete_backup,
    create_firewall,
    list_firewalls,
    get_firewall,
    update_firewall,
    delete_firewall,
    add_instance_to_firewall,
)
from app.utils.db import (
    get_db,
    convert_schedule_to_cron,
    validate_backup_schedule_inputs,
    check_connection_to_database,
)
from app.models.requests import UserCreate, UserUpdate, UserDB
from app.constants.enums import BackupStatus
from datetime import datetime
from sqlalchemy.future import select
from sqlalchemy.exc import NoResultFound
from app.constants.errors import DATABASE_NOT_FOUND_ERROR

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
async def create_database(
    db_request: DatabaseRequest, session: AsyncSession = Depends(get_db)
):

    try:

        db_id = str(uuid4())
        instance_label = get_unique_instance_name(db_id, db_request.db_name)

        new_instance_pass = str(uuid4())
        new_db_pass = str(uuid4())

        instance = create_linode_instance(
            label=instance_label,
            db_type=db_request.db_type,
            instance_root_password=new_instance_pass,
            db_root_password=new_db_pass,
            new_user=db_request.new_user,
            new_user_password=db_request.new_user_password,
            instance_type=db_request.instance_type,
            region=db_request.region,
        )

        firewall = create_firewall(
            instance_id=instance.id,
            db_type=db_request.db_type,
        )

        firewall_status = add_instance_to_firewall(
            firewall_id=firewall.get("id"),
            instance_id=instance.id,
        )

        # Store the database information in the Database table
        db_instance = Database(
            id=db_id,
            user_id=db_request.user_id,
            db_type=db_request.db_type,
            db_name=instance_label,
            db_instance_id=str(instance.id),
            instance_type=db_request.instance_type,
            region=db_request.region,
            db_root_password=new_db_pass,
            instance_root_password=new_instance_pass,
            firewall_id=firewall.get("id"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        session.add(db_instance)
        await session.commit()

        return {
            "message": "Database instance created successfully",
            "database_id": db_instance.id,
            "instance_id": db_instance.db_instance_id,
            "instance_type": db_instance.instance_type,
            "region": db_instance.region,
            "firewall_status": firewall_status,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error creating database instance: {str(e)}"
        )


@app.get("/databases/")
async def list_databases(session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(Database))
    databases = result.scalars().all()
    return [
        {
            "database_id": database.id,
            "database_name": get_instance_name_from_label(database.db_name),
            "instance_type": database.instance_type,
            "region": database.region,
            "created_at": database.created_at,
            "updated_at": database.updated_at,
        }
        for database in databases
    ]


@app.get("/databases/{database_id}")
async def get_database(database_id: str, session: AsyncSession = Depends(get_db)):
    try:
        result = await session.execute(
            select(Database).where(Database.id == database_id)
        )
        database = result.scalar_one()
        return {
            "database_id": database.id,
            "database_name": get_instance_name_from_label(database.db_name),
            "instance_type": database.instance_type,
            "region": database.region,
            "created_at": database.created_at,
            "updated_at": database.updated_at,
            "instance_status": get_instance_status(database.db_instance_id),
            "stats_status": get_linode_stats(database.db_instance_id).get(
                "status", False
            ),
            "linode_details": get_linode_instance_details(database.db_instance_id),
        }
    except NoResultFound:
        raise HTTPException(status_code=400, detail=DATABASE_NOT_FOUND_ERROR)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving database: {str(e.with_traceback())}",
        )


@app.delete("/databases/{database_id}")
async def delete_database(database_id: str, session: AsyncSession = Depends(get_db)):
    try:
        result = await session.execute(
            select(Database).where(Database.id == database_id)
        )
        database = result.scalar_one()
        delete_linode_instance(database.db_instance_id)
        await session.delete(database)
        await session.commit()
        return {"message": "Database deleted successfully"}
    except NoResultFound:
        raise HTTPException(status_code=400, detail=DATABASE_NOT_FOUND_ERROR)


@app.put("/databases/")
async def update_database(
    db_update: DatabaseUpdateRequest, session: AsyncSession = Depends(get_db)
):

    try:
        result = await session.execute(
            select(Database).where(Database.id == db_update.database_id)
        )
        database = result.scalar_one()

        if db_update.database_name:
            db_update.database_name = get_unique_instance_name(
                database.id, db_update.database_name
            )

        # # update the instance type in linode
        update_linode_instance(
            instance_name=db_update.database_name,
            instance_id=database.db_instance_id,
            instance_type=db_update.instance_type,
        )

        # Update fields
        database.db_name = db_update.database_name or database.database_name
        database.instance_type = db_update.instance_type or database.instance_type
        database.updated_at = datetime.utcnow()

        session.add(database)
        await session.commit()
        return {"message": "Database updated successfully"}
    except NoResultFound:
        raise HTTPException(status_code=400, detail="Database not found")


@app.post("/schedule_backup/")
async def schedule_backup(
    backup_request: DatabaseBackupRequest, session: AsyncSession = Depends(get_db)
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
            frequency=backup_frequency,
        ):
            raise HTTPException(
                status_code=400, detail="Invalid backup schedule parameters."
            )

        # Generate cron expression (assuming function is implemented)
        cron_expression = convert_schedule_to_cron(
            hour_of_day=backup_hour_of_day,
            day_of_week=backup_day_of_week,
            day_of_month=backup_day_of_month,
            frequency=backup_frequency,
        )

        # Get the database instance
        database = await session.get(Database, database_id)

        status = deploy_backup_script(
            database_id=database_id,
            user_id=database.user_id,
            instance_id=database.db_instance_id,
            cron_schedule=cron_expression,
            db_type=database.db_type,
            ssh_password=database.instance_root_password,
            db_password=database.db_root_password,
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
            updated_at=datetime.utcnow(),
        )
        session.add(new_backup_schedule)
        await session.commit()

        return {
            "message": "Backup schedule created successfully",
            "schedule_id": new_backup_schedule.id,
            "status": status,
        }
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error scheduling backup: {str(e)}"
        )


@app.get("/databases/{database_id}/stats")
async def get_database_stats(database_id: str, session: AsyncSession = Depends(get_db)):
    try:

        result = await session.execute(
            select(Database).where(Database.id == database_id)
        )
        database = result.scalar_one()
        stats = get_linode_stats(database.db_instance_id)

        return stats

    except NoResultFound:
        raise HTTPException(status_code=400, detail=DATABASE_NOT_FOUND_ERROR)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving stats: {str(e)}")


@app.get("/databases/{database_id}/health")
async def get_database_health(
    database_id: str, session: AsyncSession = Depends(get_db)
):
    try:

        result = await session.execute(
            select(Database).where(Database.id == database_id)
        )
        database = result.scalar_one()

        stats = get_linode_stats(database.db_instance_id)
        instance_status = get_instance_status(database.db_instance_id)

        # NOTE implement later
        # db_connection_status = check_connection_to_database(
        #     db_type=database.db_type,
        #     instance_id=database.db_instance_id,
        #     password=database.db_root_password,
        # )

        return {
            "status": instance_status,
            "stats": stats,
            # "db_connection_status": db_connection_status,
        }

    except NoResultFound:
        raise HTTPException(status_code=400, detail=DATABASE_NOT_FOUND_ERROR)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving stats: {str(e)}")


@app.get("/databases/{database_id}/backups")
async def get_database_backups(
    database_id: str, session: AsyncSession = Depends(get_db)
):
    try:

        result = await session.execute(
            select(Database).where(Database.id == database_id)
        )
        database = result.scalar_one()

        backups = get_backups(
            database_type=database.db_type,
            user_id=database.user_id,
            db_id=database.id,
        )

        return {"backups": backups}

    except NoResultFound:
        raise HTTPException(status_code=400, detail=DATABASE_NOT_FOUND_ERROR)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving backups: {str(e)}"
        )


@app.delete("/backups")
async def delete_database_backup(
    request: DatabaseBackupDeleteRequest,
    session: AsyncSession = Depends(get_db),
):

    try:
        status = delete_backup(
            backup_id=request.backup_id,
        )

        return {"status": status}
    except NoResultFound:
        raise HTTPException(status_code=400, detail=DATABASE_NOT_FOUND_ERROR)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting backup: {str(e)}")


@app.get("/firewalls/")
async def list_firewalls_endpoint(user_id: str = None, db_id: str = None):
    try:
        firewalls = list_firewalls(user_id=user_id, db_id=db_id)
        return {"firewalls": firewalls}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error listing firewalls: {str(e)}"
        )


@app.get("/firewalls/{firewall_id}")
async def get_firewall_endpoint(firewall_id: int):
    try:
        firewall = get_firewall(firewall_id)
        return {"firewall": firewall}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving firewall: {str(e)}"
        )


@app.put("/firewalls/{firewall_id}")
async def update_firewall_endpoint(
    firewall_id: int, firewall_update: FirewallUpdateRequest
):
    try:
        firewall = update_firewall(
            firewall_id=firewall_id,
            label=firewall_update.label,
            rules=firewall_update.rules,
        )
        return {"message": "Firewall updated successfully", "firewall": firewall}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error updating firewall: {str(e)}"
        )


@app.delete("/firewalls/{firewall_id}")
async def delete_firewall_endpoint(firewall_id: int):
    try:
        success = delete_firewall(firewall_id)
        if success:
            return {"message": "Firewall deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Error deleting firewall")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error deleting firewall: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
