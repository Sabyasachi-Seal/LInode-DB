from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.models.base import Base
from app.models.database import Database
from app.requests.requests import DatabaseRequest
from app.auth.auth import auth_backends, fastapi_users
from app.utils.linode import create_linode_instance
from app.utils.db import get_db

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the FastAPI Users routes
app.include_router(
    fastapi_users.get_auth_router(auth_backends[0]),
    prefix="/auth/jwt",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_register_router(),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_users_router(),
    prefix="/users",
    tags=["users"],
)

@app.post("/create_database/")
async def create_database(db_request: DatabaseRequest, user=Depends(fastapi_users.get_current_active_user), session: AsyncSession = Depends(get_db)):
    try:
        # Create the Linode instance
        instance = create_linode_instance(
            label=f"{db_request.db_type}-instance",
            db_type=db_request.db_type,
            db_root_password=db_request.db_root_password,
            new_user=db_request.new_user,
            new_user_password=db_request.new_user_password,
            new_db=db_request.new_db,
            instance_type=db_request.instance_type,
            region=db_request.region
        )

        # Store the database information in the Database table
        db_instance = Database(
            id=str(uuid4()),
            user_id=user.id,
            db_type=db_request.db_type,
            db_name=db_request.new_db,
            db_instance_id=str(instance.id),
            instance_type=db_request.instance_type,
            region=db_request.region,
            backup_schedule=db_request.backup_schedule if db_request.backup_schedule else None
        )
        session.add(db_instance)
        await session.commit()

        return {"message": "Database instance created successfully", "instance_id": instance.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating database instance: {str(e)}")