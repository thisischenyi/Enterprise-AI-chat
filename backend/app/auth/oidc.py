"""Mock OIDC provider — adapter pattern for mock auth flow.

This stub will be implemented in Task 2 to handle:
- Token signing with itsdangerous TimedSerializer
- User creation/lookup for mock test users
- Session creation with signed tokens
"""


class MockOIDCProvider:
    """Mock OIDC provider stub — placeholder for Task 2 implementation."""

    def initiate_login(self, role: str) -> dict[str, str]:
        """Stub: returns placeholder login response."""
        return {"redirect_url": "/mock-login", "role": role}

    def handle_callback(self, mock_state_token: str, role: str) -> dict[str, str]:
        """Stub: returns placeholder callback response."""
        return {"message": "Mock callback stub"}

    def validate_token(self, token: str) -> bool:
        """Stub: returns placeholder validation response."""
        return False