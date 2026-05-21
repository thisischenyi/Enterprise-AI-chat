"""Shared test database fixtures — conftest.py.

Provides a single in-memory SQLite database (aiosqlite) for all backend tests,
seeded with mock users (employee and admin). This avoids the conflict that
occurs when multiple test files each create their own database override on
the same FastAPI app object — only one override can be active at a time.

Uses dependency_overrides pattern so production PostgreSQL (asyncpg) is not
affected. Tests override get_db_session with a test SQLite session factory.
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import get_db_session
from app.db.schema import Base, Session, User
from app.main import app

# Shared test database: in-memory SQLite with aiosqlite driver
TEST_DATABASE_URL = "sqlite+aiosqlite://"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionFactory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db_session() -> AsyncSession:
    """Override DB dependency for tests — yields test SQLite session."""
    session = TestSessionFactory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


# Override the production DB dependency with test DB (shared across all tests)
app.dependency_overrides[get_db_session] = override_get_db_session


MOCK_USERS = [
    {
        "email": "employee@test-enterprise.com",
        "name": "Test Employee",
        "role": "employee",
    },
    {
        "email": "admin@test-enterprise.com",
        "name": "Test Admin",
        "role": "admin",
    },
]


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    """Create tables and seed mock users once per test session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionFactory() as session:
        for user_data in MOCK_USERS:
            user = User(**user_data)
            session.add(user)
        await session.commit()

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await test_engine.dispose()


@pytest_asyncio.fixture
async def client():
    """Async HTTP client for testing FastAPI app with DB override."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def clean_sessions():
    """Clean up session rows between tests."""
    async with TestSessionFactory() as session:
        from sqlalchemy import delete as sa_delete
        await session.execute(sa_delete(Session))
        await session.commit()
    yield
    async with TestSessionFactory() as session:
        from sqlalchemy import delete as sa_delete
        await session.execute(sa_delete(Session))
        await session.commit()