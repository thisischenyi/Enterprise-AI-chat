"""Chat API endpoint integration tests.

Tests POST /api/chat/send and GET /api/chat/models with mock model provider
and mock safety pipeline scanners. Verifies auth enforcement.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch

from app.api.chat import get_safety_pipeline
from app.main import app
from app.models.providers import ModelProvider, ProviderRegistry, get_provider_registry
from app.safety.pipeline import SafetyPipeline
from app.safety.policy import SafetyPolicy
from app.tests.test_fixtures import MockDataProtectionScanner, MockLLMGuardrailScanner


# --- Mock model provider ---


class MockModelProvider(ModelProvider):
    """Mock provider that returns fixed responses without calling real APIs."""

    provider_id = "mock"
    model_id = "mock-model"
    display_name = "Mock Model"
    description = "Test model for unit tests"

    def __init__(self, response: str = "This is a test model response"):
        self._response = response

    async def chat_completion(self, messages: list[dict[str, str]]) -> str:
        return self._response


class MockProviderRegistry(ProviderRegistry):
    """Registry with a mock provider pre-loaded."""

    def __init__(self, provider: MockModelProvider | None = None):
        # Skip parent __init__ which reads env vars
        self._providers = {}
        self._display_names = {}
        p = provider or MockModelProvider()
        self._providers[p.model_id] = p
        self._display_names[p.model_id] = p.display_name

    def _init_providers(self) -> None:
        pass


# --- Dependency overrides ---


def get_mock_pipeline() -> SafetyPipeline:
    """Pipeline with mock scanners for testing."""
    return SafetyPipeline(
        scanners=[MockDataProtectionScanner(score_threshold=0.0), MockLLMGuardrailScanner(min_confidence=0.0)],
        policy=SafetyPolicy(),
        timeout=30.0,
    )


def get_mock_registry() -> MockProviderRegistry:
    return MockProviderRegistry()


# Apply overrides at fixture level, not module level, to avoid polluting other tests


# --- Fixtures ---


@pytest.fixture(autouse=True)
def _override_deps():
    """Override safety pipeline and provider registry for chat tests only."""
    app.dependency_overrides[get_safety_pipeline] = get_mock_pipeline
    app.dependency_overrides[get_provider_registry] = get_mock_registry
    yield
    app.dependency_overrides.pop(get_safety_pipeline, None)
    app.dependency_overrides.pop(get_provider_registry, None)


# --- Helper ---


async def _get_auth_cookie(client: AsyncClient) -> str:
    """Create a session and return the session_id cookie."""
    login = await client.post("/api/auth/login", params={"role": "employee"})
    state_token = login.json()["state_token"]
    callback = await client.post(
        "/api/auth/callback",
        params={"role": "employee", "state_token": state_token},
    )
    return callback.cookies.get("session_id")


# --- Tests ---


@pytest.mark.asyncio
async def test_chat_send_allowed(client: AsyncClient, clean_sessions):
    """POST /api/chat/send with safe message returns allowed response."""
    cookie = await _get_auth_cookie(client)
    response = await client.post(
        "/api/chat/send",
        json={"message": "What is the weather in Beijing?", "model_id": "mock-model"},
        cookies={"session_id": cookie},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "allowed"
    assert data["content"] == "This is a test model response"
    assert data["model_id"] == "mock-model"


@pytest.mark.asyncio
async def test_chat_send_input_blocked(client: AsyncClient, clean_sessions):
    """POST /api/chat/send with PII message returns blocked response."""
    cookie = await _get_auth_cookie(client)
    response = await client.post(
        "/api/chat/send",
        json={"message": "My SSN is 123-45-6789", "model_id": "mock-model"},
        cookies={"session_id": cookie},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "blocked"
    # Block message must NOT echo raw PII
    assert "123-45-6789" not in data["content"]
    assert "pii" in data["risk_categories"]


@pytest.mark.asyncio
async def test_chat_send_fail_closed(client: AsyncClient, clean_sessions):
    """POST /api/chat/send when scanner crashes returns fail_closed."""
    from app.safety.pipeline import SafetyPipeline
    from app.safety.policy import SafetyPolicy

    class CrashScanner:
        async def scan(self, content, source):
            raise RuntimeError("boom")

    def get_crashing_pipeline():
        return SafetyPipeline(scanners=[CrashScanner()], policy=SafetyPolicy(), timeout=30.0)

    app.dependency_overrides[get_safety_pipeline] = get_crashing_pipeline
    try:
        cookie = await _get_auth_cookie(client)
        response = await client.post(
            "/api/chat/send",
            json={"message": "Hello", "model_id": "mock-model"},
            cookies={"session_id": cookie},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "fail_closed"
        assert "system error" in data["content"].lower()
    finally:
        app.dependency_overrides[get_safety_pipeline] = get_mock_pipeline


@pytest.mark.asyncio
async def test_chat_models(client: AsyncClient, clean_sessions):
    """GET /api/chat/models returns available models."""
    cookie = await _get_auth_cookie(client)
    response = await client.get(
        "/api/chat/models",
        cookies={"session_id": cookie},
    )
    assert response.status_code == 200
    models = response.json()
    assert len(models) >= 1
    assert models[0]["id"] == "mock-model"
    assert models[0]["name"] == "Mock Model"


@pytest.mark.asyncio
async def test_chat_send_unauthenticated(client: AsyncClient):
    """POST /api/chat/send without session returns 401."""
    response = await client.post(
        "/api/chat/send",
        json={"message": "Hello", "model_id": "mock-model"},
    )
    assert response.status_code == 401
