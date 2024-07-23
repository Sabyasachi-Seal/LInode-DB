from fastapi import Depends
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import JWTAuthentication
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.user import User
from app.models.user_schemas import UserCreate, UserUpdate, UserDB

DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(DATABASE_URL, echo=True)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_user_db(session: AsyncSession = Depends(async_session_maker)):
    yield SQLAlchemyUserDatabase(session, User)

SECRET = "SECRET"

auth_backends = [
    JWTAuthentication(secret=SECRET, lifetime_seconds=3600, tokenUrl="auth/jwt/login"),
]

fastapi_users = FastAPIUsers(
    get_user_db,
    auth_backends,
    User,
    UserCreate,
    UserUpdate,
    UserDB,
)