"""Role-based access control integration tests — RED phase.

Tests verify that role enforcement works at both the API endpoint level:
1. Admin user GET /api/admin/config returns 200 OK
2. Employee user GET /api/admin/config returns 403 Forbidden
3. Unauthenticated GET /api/admin/config returns 401 Unauthorized
4. Employee user GET /api/chat/models returns 200 OK
5. Admin user GET /api/chat/models returns 200 OK
6. Unauthenticated GET /api/chat/models returns 401 Unauthorized

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
async def authenticated_admin_client(client: AsyncClient):
    """Client with admin session cookie — authenticated as admin user."""
    # Login as admin to get state token
    login_response = await client.post("/api/auth/login", params={"role": "admin"})
    state_token = login_response.json()["state_token"]

    # Callback to create session and get cookie
    callback_response = await client.post(
        "/api/auth/callback",
        params={"role": "admin", "state_token": state_token},
    )
    session_cookie = callback_response.cookies.get("session_id")
    assert session_cookie is not None, "Admin callback should set session cookie"

    # Return client with admin session cookie attached
    client.cookies.set("session_id", session_cookie)
    return client


@pytest_asyncio.fixture
async def authenticated_employee_client(client: AsyncClient):
    """Client with employee session cookie — authenticated as employee user."""
    # Login as employee to get state token
    login_response = await client.post("/api/auth/login", params={"role": "employee"})
    state_token = login_response.json()["state_token"]

    # Callback to create session and get cookie
    callback_response = await client.post(
        "/api/auth/callback",
        params={"role": "employee", "state_token": state_token},
    )
    session_cookie = callback_response.cookies.get("session_id")
    assert session_cookie is not None, "Employee callback should set session cookie"

    # Return client with employee session cookie attached
    client.cookies.set("session_id", session_cookie)
    return client


@pytest_asyncio.fixture
async def unauthenticated_client(client: AsyncClient):
    """Client with no session cookie — unauthenticated."""
    # Clear any cookies that might have been set by other fixtures
    client.cookies.clear()
    return client


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
async def test_admin_access_admin_endpoint(authenticated_admin_client: AsyncClient, clean_sessions):
    """Test 1: Admin user GET /api/admin/config returns 200 OK — admin role grants access."""
    response = await authenticated_admin_client.get("/api/admin/config")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["user_role"] == "admin"


@pytest.mark.asyncio
async def test_employee_forbidden_admin_endpoint(authenticated_employee_client: AsyncClient, clean_sessions):
    """Test 2: Employee user GET /api/admin/config returns 403 Forbidden — employee role rejected."""
    response = await authenticated_employee_client.get("/api/admin/config")
    assert response.status_code == 403
    data = response.json()
    assert data["detail"] == "Admin access required"


@pytest.mark.asyncio
async def test_unauthenticated_admin_endpoint(unauthenticated_client: AsyncClient):
    """Test 3: Unauthenticated GET /api/admin/config returns 401 Unauthorized."""
    response = await unauthenticated_client.get("/api/admin/config")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_employee_access_chat_endpoint(authenticated_employee_client: AsyncClient, clean_sessions):
    """Test 4: Employee user GET /api/chat/models returns 200 OK — employee can access chat."""
    response = await authenticated_employee_client.get("/api/chat/models")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["user_role"] == "employee"


@pytest.mark.asyncio
async def test_admin_access_chat_endpoint(authenticated_admin_client: AsyncClient, clean_sessions):
    """Test 5: Admin user GET /api/chat/models returns 200 OK — admin can also access chat."""
    response = await authenticated_admin_client.get("/api/chat/models")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["user_role"] == "admin"


@pytest.mark.asyncio
async def test_unauthenticated_chat_endpoint(unauthenticated_client: AsyncClient):
    """Test 6: Unauthenticated GET /api/chat/models returns 401 Unauthorized."""
    response = await unauthenticated_client.get("/api/chat/models")
    assert response.status_code == 401