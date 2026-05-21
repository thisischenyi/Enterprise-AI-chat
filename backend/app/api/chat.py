"""Chat API routes — Phase 2 placeholder."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def chat_stub() -> dict[str, str]:
    """Phase 2 placeholder — chat endpoint."""
    return {"message": "Chat endpoint - Phase 2"}