"""Auth API routes — mock OIDC login, callback, and current user endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.auth.current_user import get_current_user
from app.db.schema import User

router = APIRouter()


@router.post("/login")
async def login(role: str = "employee") -> dict[str, str]:
    """Initiate mock OIDC login flow. Returns redirect URL for frontend."""
    # Stub: returns placeholder redirect — will be implemented in Task 2
    return {"redirect_url": "/mock-login", "role": role, "message": "Mock OIDC login stub"}


@router.post("/callback")
async def callback(role: str = "employee") -> dict[str, str]:
    """Mock OIDC callback — creates session and returns session cookie."""
    # Stub: returns placeholder response — will be implemented in Task 2
    return {"message": "Mock OIDC callback stub"}


@router.get("/me")
async def me(current_user: User = Depends(get_current_user)) -> dict[str, str]:
    """Return current authenticated user identity."""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "name": current_user.name,
        "role": current_user.role,
    }