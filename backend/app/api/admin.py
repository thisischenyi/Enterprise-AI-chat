"""Admin API routes — admin-only endpoints with role enforcement.

Admin endpoints require Depends(get_admin_user) which checks user.role == "admin"
and raises 403 for non-admin users (per AUTH-03 and threat model T-01-04, T-01-10).
403 response contains only generic "Admin access required" message — no user
identity or role enumeration hints (per T-01-10).
"""

from fastapi import APIRouter, Depends

from app.auth.current_user import get_admin_user
from app.db.schema import User

router = APIRouter()


@router.get("/config")
async def admin_config(current_user: User = Depends(get_admin_user)) -> dict[str, str]:
    """Admin configuration endpoint — Phase 4 placeholder.

    Only accessible to admin-role users. Returns role confirmation.
    Employee and unauthenticated users receive 403/401 respectively.
    """
    return {
        "message": "Admin configuration endpoint - Phase 4",
        "user_role": current_user.role,
    }