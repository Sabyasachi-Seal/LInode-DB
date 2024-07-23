from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
from uuid import uuid4

from app.models.base import Base
from app.models.database import Database
from app.auth.auth import auth_backends, fastapi_users
from app.utils.linode_utils import create_linode_instance
from app.config import settings

DATABASE_URL = f"mysql+aiomysql://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"

engine = create_async_engine(DATABASE_URL, echo=True)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

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

# Database creation request model
class DatabaseRequest(BaseModel):
    db_type: str  # "mysql", "postgresql", or "mongodb"
    db_root_password: str
    new_user: str
    new_user_password: str
    new_db: str  # Only used for PostgreSQL and MongoDB

@app.post("/create_database/")
async def create_database(db_request: DatabaseRequest, user=Depends(fastapi_users.get_current_active_user), session: AsyncSession = Depends(async_session_maker)):
    try:
        # Create the Linode instance
        instance = create_linode_instance(
            label=f"{db_request.db_type}-instance",
            db_type=db_request.db_type,
            db_root_password=db_request.db_root_password,
            new_user=db_request.new_user,
            new_user_password=db_request.new_user_password,
            new_db=db_request.new_db
        )

        # Store the database information in the Database table
        db_instance = Database(
            id=str(uuid4()),
            user_id=user.id,
            db_type=db_request.db_type,
            db_name=db_request.new_db,
            db_instance_id=str(instance.id),
            backup_config=None  # Add backup config if needed
        )
        session.add(db_instance)
        await session.commit()

        return {"message": "Database instance created successfully", "instance_id": instance.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating database instance: {str(e)}")