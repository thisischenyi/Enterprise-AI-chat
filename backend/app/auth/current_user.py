"""Current user dependency — FastAPI Depends for authenticated user identity.

This stub returns HTTPException 401 for all requests.
Task 2 will implement session validation via DB lookup.
"""

from fastapi import Depends, HTTPException, status


async def get_current_user() -> None:
    """Stub: always raises 401 — will be implemented in Task 2."""
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
    )


async def get_admin_user() -> None:
    """Stub: always raises 401 — will be implemented in Task 2."""
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
    )