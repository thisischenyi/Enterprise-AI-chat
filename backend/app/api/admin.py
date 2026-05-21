"""Admin API routes — Phase 4 placeholder."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def admin_stub() -> dict[str, str]:
    """Phase 4 placeholder — admin endpoint."""
    return {"message": "Admin endpoint - Phase 4"}