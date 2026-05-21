"""Authentication integration tests — RED phase.

Tests verify the auth pipeline works end-to-end:
1. GET /api/auth/me with valid session returns user identity
2. GET /api/auth/me without session returns 401
3. POST /api/auth/callback creates session and returns cookie

Currently these tests FAIL because auth middleware is a stub
that always raises 401. Task 2 will implement the middleware
to make these tests pass (GREEN phase).
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest_asyncio.fixture
async def client():
    """Async HTTP client for testing FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_me_with_valid_session_returns_user_identity(client: AsyncClient):
    """Test 1: GET /api/auth/me with valid session cookie returns authenticated user identity.

    This test FAILS in the RED phase because get_current_user always raises 401.
    It will PASS in the GREEN phase after auth middleware is implemented.
    """
    # First, create a session via callback
    callback_response = await client.post(
        "/api/auth/callback",
        params={"role": "employee"},
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


@pytest.mark.asyncio
async def test_me_without_session_returns_401(client: AsyncClient):
    """Test 2: GET /api/auth/me without session cookie returns 401 Unauthorized.

    This test PASSES in RED phase because the stub always returns 401.
    It should continue to PASS in GREEN phase.
    """
    response = await client.get("/api/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_callback_creates_session(client: AsyncClient):
    """Test 3: POST /api/auth/callback with valid mock auth creates session and returns cookie.

    This test FAILS in RED phase because callback is a stub.
    It will PASS in GREEN phase after mock OIDC is implemented.
    """
    response = await client.post(
        "/api/auth/callback",
        params={"role": "employee"},
    )

    # Should create session and return session cookie
    assert response.status_code == 200

    # Session cookie should be set
    session_cookie = response.cookies.get("session_id")
    assert session_cookie is not None, "Callback should set session_id cookie"

    # Response should contain user info or redirect
    data = response.json()
    assert "message" not in data or data.get("message") != "Mock OIDC callback stub"