"""Mock OIDC provider — adapter pattern for mock auth flow.

Uses itsdangerous TimedSerializer for token signing (per D-01/D-03).
Wraps behind OIDCProvider protocol so real IDP can be swapped in later.
"""

import os
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone

from itsdangerous import SignatureExpired, TimedSerializer


class OIDCProvider(ABC):
    """Abstract OIDC provider interface — future real IDP adapter implements this."""

    @abstractmethod
    def initiate_login(self, role: str) -> dict[str, str]:
        """Start OIDC login flow, return redirect URL and state token."""
        ...

    @abstractmethod
    def handle_callback(self, state_token: str, role: str) -> dict[str, str]:
        """Handle OIDC callback, validate state, return user info."""
        ...

    @abstractmethod
    def validate_token(self, token: str) -> bool:
        """Validate a session token signature and expiry."""
        ...


# Map role to mock test user email and name
MOCK_USERS = {
    "employee": {
        "email": "employee@test-enterprise.com",
        "name": "Test Employee",
    },
    "admin": {
        "email": "admin@test-enterprise.com",
        "name": "Test Admin",
    },
}

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-this")
TOKEN_MAX_AGE = 3600  # 1 hour


class MockOIDCProvider(OIDCProvider):
    """Mock OIDC provider — simulates OIDC flow with itsdangerous token signing.

    Uses TimedSerializer to sign state tokens (for callback validation)
    and session tokens (for session cookie validation).
    """

    def __init__(self, secret_key: str = SECRET_KEY, max_age: int = TOKEN_MAX_AGE):
        self.serializer = TimedSerializer(secret_key)
        self.max_age = max_age

    def initiate_login(self, role: str) -> dict[str, str]:
        """Generate mock state token signed with itsdangerous.

        Returns redirect_url (for frontend mock login page) and state_token
        that the frontend passes back on callback.
        """
        # Create signed state token containing role info
        state_data = {"role": role, "nonce": str(uuid.uuid4())}
        state_token = self.serializer.dumps(state_data)

        return {
            "redirect_url": "/mock-login",
            "state_token": state_token,
            "role": role,
        }

    def handle_callback(self, state_token: str, role: str) -> dict[str, str]:
        """Validate state token and return user info + session token.

        Validates the signed state token from the login step.
        Returns mock user info based on role parameter and a signed
        session token for the session cookie.
        """
        # Validate the state token signature
        try:
            state_data = self.serializer.loads(state_token, max_age=self.max_age)
        except SignatureExpired:
            raise ValueError("State token expired")
        except Exception:
            raise ValueError("Invalid state token")

        # Get mock user info based on role
        user_info = MOCK_USERS.get(role, MOCK_USERS["employee"])

        # Generate session token
        session_data = {
            "role": role,
            "email": user_info["email"],
            "nonce": str(uuid.uuid4()),
        }
        session_token = self.serializer.dumps(session_data)

        return {
            "email": user_info["email"],
            "name": user_info["name"],
            "role": role,
            "session_token": session_token,
        }

    def validate_token(self, token: str) -> bool:
        """Validate session token signature and expiry.

        Returns True if token is valid and not expired, False otherwise.
        """
        try:
            self.serializer.loads(token, max_age=self.max_age)
            return True
        except (SignatureExpired, Exception):
            return False