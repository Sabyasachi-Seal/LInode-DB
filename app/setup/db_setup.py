from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, exists
from app.models.base import Base
from app.models.user import User
from app.config import settings

DATABASE_URL = f"mysql+aiomysql://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"

engine = create_async_engine(DATABASE_URL, echo=True)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def drop_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

async def seed_initial_data():
    async with async_session_maker() as session:
        async with session.begin():
            # Check if initial data exists
            user_exists = await session.execute(select(exists().where(User.email == "admin@example.com")))
            if not user_exists.scalar():
                # Seed initial user
                user = User(
                    id="1",
                    email=settings.init_email,
                    hashed_password=settings.init_pass,  # Replace with a properly hashed password
                    is_active=True,
                    is_superuser=True
                )
                session.add(user)

async def apply_migrations():
    async with engine.begin() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS test_table (id INT PRIMARY KEY AUTO_INCREMENT, name VARCHAR(255))")

async def main():
    await create_db_and_tables()
    await seed_initial_data()
    await apply_migrations()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())