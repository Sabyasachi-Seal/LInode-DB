# app/auth/manager.py
from typing import Optional
from fastapi import Request, Depends
from fastapi_users import BaseUserManager, UUIDIDMixin
from fastapi_users.db import SQLAlchemyUserDatabase
from app.models.requests import UserDB, UserCreate
from app.config import settings

class UserManager(UUIDIDMixin, BaseUserManager[UserDB, UserCreate]):
    user_db_model = UserDB

    async def on_after_register(self, user: UserDB, request: Optional[Request] = None):
        print(f"User {user.id} has registered.")

    async def on_after_forgot_password(
        self, user: UserDB, token: str, request: Optional[Request] = None
    ):
        print(f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_update(self, user: UserDB, update_dict: dict, request: Optional[Request] = None):
        print(f"User {user.id} has been updated with {update_dict}.")

