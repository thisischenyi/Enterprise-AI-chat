"""Chat API routes — authenticated endpoints requiring any authenticated user.

Chat endpoints require Depends(get_current_user) which validates session
and returns authenticated User (per AUTH-02). Both employee and admin roles
can access chat endpoints — only admin endpoints restrict to admin role.
"""

from fastapi import APIRouter, Depends

from app.auth.current_user import get_current_user
from app.db.schema import User

router = APIRouter()


@router.get("/models")
async def chat_models(current_user: User = Depends(get_current_user)) -> dict[str, str]:
    """Chat models endpoint — Phase 2 placeholder.

    Accessible to any authenticated user (employee or admin).
    Unauthenticated users receive 401.
    """
    return {
        "message": "Chat models endpoint - Phase 2",
        "user_role": current_user.role,
    }