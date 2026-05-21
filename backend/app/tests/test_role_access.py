"""Role-based access control integration tests.

Tests verify that role enforcement works at the API endpoint level:
1. Admin user GET /api/admin/config returns 200 OK
2. Employee user GET /api/admin/config returns 403 Forbidden
3. Unauthenticated GET /api/admin/config returns 401 Unauthorized
4. Employee user GET /api/chat/models returns 200 OK
5. Admin user GET /api/chat/models returns 200 OK
6. Unauthenticated GET /api/chat/models returns 401 Unauthorized

Uses shared test database from conftest.py (SQLite via aiosqlite).
Production uses PostgreSQL (asyncpg) — same SQLAlchemy models work on both.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient

from app.db.schema import Session
from app.tests.conftest import TestSessionFactory


@pytest_asyncio.fixture
async def authenticated_admin_client(client: AsyncClient, clean_sessions):
    """Client with admin session cookie — authenticated as admin user.

    Depends on clean_sessions so sessions are cleared BEFORE this fixture
    creates its own session, preventing the cleanup from deleting the
    active session mid-test.
    """
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
async def authenticated_employee_client(client: AsyncClient, clean_sessions):
    """Client with employee session cookie — authenticated as employee user.

    Depends on clean_sessions so sessions are cleared BEFORE this fixture
    creates its own session, preventing the cleanup from deleting the
    active session mid-test.
    """
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
    client.cookies.clear()
    return client


@pytest.mark.asyncio
async def test_admin_access_admin_endpoint(authenticated_admin_client: AsyncClient):
    """Test 1: Admin user GET /api/admin/config returns 200 OK — admin role grants access."""
    response = await authenticated_admin_client.get("/api/admin/config")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["user_role"] == "admin"


@pytest.mark.asyncio
async def test_employee_forbidden_admin_endpoint(authenticated_employee_client: AsyncClient):
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
async def test_employee_access_chat_endpoint(authenticated_employee_client: AsyncClient):
    """Test 4: Employee user GET /api/chat/models returns 200 OK — employee can access chat."""
    response = await authenticated_employee_client.get("/api/chat/models")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["user_role"] == "employee"


@pytest.mark.asyncio
async def test_admin_access_chat_endpoint(authenticated_admin_client: AsyncClient):
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