"""Authentication integration tests — GREEN phase.

Tests verify the auth pipeline works end-to-end:
1. GET /api/auth/me with valid session returns user identity
2. GET /api/auth/me without session returns 401
3. POST /api/auth/callback creates session and returns cookie

Uses SQLite (aiosqlite) for testing via FastAPI dependency override.
Production uses PostgreSQL (asyncpg) — same SQLAlchemy models work on both.
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import get_db_session
from app.db.schema import Base, Session, User
from app.main import app

# Test database: in-memory SQLite with aiosqlite driver
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


# Override the production DB dependency with test DB
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
        from sqlalchemy import delete
        await session.execute(delete(Session))
        await session.commit()
    yield
    async with TestSessionFactory() as session:
        from sqlalchemy import delete
        await session.execute(delete(Session))
        await session.commit()


@pytest.mark.asyncio
async def test_me_with_valid_session_returns_user_identity(client: AsyncClient, clean_sessions):
    """Test 1: GET /api/auth/me with valid session cookie returns authenticated user identity.

    GREEN phase: callback creates session and sets cookie, /me returns user.
    """
    # First, get a state token via login
    login_response = await client.post("/api/auth/login", params={"role": "employee"})
    assert login_response.status_code == 200
    state_token = login_response.json()["state_token"]

    # Then, create a session via callback with the state token
    callback_response = await client.post(
        "/api/auth/callback",
        params={"role": "employee", "state_token": state_token},
    )
    assert callback_response.status_code == 200

    # Extract session cookie from callback response
    session_cookie = callback_response.cookies.get("session_id")
    assert session_cookie is not None, "Callback should set session_id cookie"

    # Then, call /me with the session cookie
    me_response = await client.get(
        "/api/auth/me",
        cookies={"session_id": session_cookie},
    )

    # Should return authenticated user identity
    assert me_response.status_code == 200
    user_data = me_response.json()
    assert "id" in user_data
    assert "email" in user_data
    assert "name" in user_data
    assert "role" in user_data
    assert user_data["role"] == "employee"
    assert user_data["email"] == "employee@test-enterprise.com"


@pytest.mark.asyncio
async def test_me_without_session_returns_401(client: AsyncClient):
    """Test 2: GET /api/auth/me without session cookie returns 401 Unauthorized.

    GREEN phase: auth middleware correctly rejects unauthenticated requests.
    """
    response = await client.get("/api/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_callback_creates_session(client: AsyncClient, clean_sessions):
    """Test 3: POST /api/auth/callback creates session and returns session cookie.

    GREEN phase: mock OIDC callback works end-to-end.
    """
    # Get a valid state token via login
    login_response = await client.post("/api/auth/login", params={"role": "employee"})
    state_token = login_response.json()["state_token"]

    response = await client.post(
        "/api/auth/callback",
        params={"role": "employee", "state_token": state_token},
    )

    # Should create session and return session cookie
    assert response.status_code == 200

    # Session cookie should be set
    session_cookie = response.cookies.get("session_id")
    assert session_cookie is not None, "Callback should set session_id cookie"

    # Response should contain user identity (not stub message)
    data = response.json()
    assert "id" in data
    assert "email" in data
    assert data["email"] == "employee@test-enterprise.com"
    assert data["role"] == "employee"