from fastapi import Depends
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import JWTAuthentication
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import Base
from app.models.user import User
from app.requests.requests import UserCreate, UserUpdate, UserDB
from app.config import settings
from app.utils.db import get_db

SECRET = settings.secret_key

async def get_user_db(session: AsyncSession = Depends(get_db)):
    yield SQLAlchemyUserDatabase(session, User)


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