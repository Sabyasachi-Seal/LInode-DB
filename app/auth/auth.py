# app/auth/auth.py
from fastapi import Depends
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import (
    CookieTransport,
    JWTStrategy,
    AuthenticationBackend,
)
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.requests import UserCreate, UserUpdate, UserDB
from app.config import settings
from app.utils.db import get_db
from app.auth.manager import UserManager


async def get_user_db(session: AsyncSession = Depends(get_db)):
    yield SQLAlchemyUserDatabase(UserDB, session, User)

def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)

# Define the transport
cookie_transport = CookieTransport(cookie_max_age=3600)

# Define the JWT strategy
SECRET = settings.secret_key

def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)

# Define the authentication backend
auth_backend = AuthenticationBackend(
    name="jwt",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)

# Initialize FastAPIUsers
fastapi_users = FastAPIUsers[UserDB, UserCreate](
    get_user_manager,
    [auth_backend],
)

current_active_user = fastapi_users.current_user(active=True)