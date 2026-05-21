"""Seed data — creates 2 mock test users for mock OIDC authentication.

Test users:
- employee@test-enterprise.com (role=employee)
- admin@test-enterprise.com (role=admin)
"""

import asyncio
import uuid

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.schema import Base, User

EMPLOYEE_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
ADMIN_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")

TEST_USERS = [
    {
        "id": EMPLOYEE_USER_ID,
        "email": "employee@test-enterprise.com",
        "name": "Test Employee",
        "role": "employee",
    },
    {
        "id": ADMIN_USER_ID,
        "email": "admin@test-enterprise.com",
        "name": "Test Admin",
        "role": "admin",
    },
]


async def seed_users(database_url: str) -> None:
    """Insert mock test users into the database."""
    engine = create_async_engine(database_url, echo=True)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        for user_data in TEST_USERS:
            # Check if user already exists
            from sqlalchemy import select
            result = await session.execute(select(User).where(User.email == user_data["email"]))
            existing = result.scalar_one_or_none()
            if existing is None:
                user = User(**user_data)
                session.add(user)

        await session.commit()

    await engine.dispose()


def main() -> None:
    import os
    from dotenv import load_dotenv

    load_dotenv()
    database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:password@localhost:5432/enterprise_chat_mvp")
    asyncio.run(seed_users(database_url))


if __name__ == "__main__":
    main()