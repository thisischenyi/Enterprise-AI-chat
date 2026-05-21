"""Authentication integration tests.

Tests verify the auth pipeline works end-to-end:
1. GET /api/auth/me with valid session returns user identity
2. GET /api/auth/me without session returns 401
3. POST /api/auth/callback creates session and returns cookie

Uses shared test database from conftest.py (SQLite via aiosqlite).
Production uses PostgreSQL (asyncpg) — same SQLAlchemy models work on both.
"""

import pytest
from httpx import AsyncClient


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