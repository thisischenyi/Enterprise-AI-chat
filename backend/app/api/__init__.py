"""API module — route registration for auth, chat, and admin endpoints."""

from app.api.auth import router as auth_router

# Phase 2 placeholder: chat router will be imported here
# Phase 4 placeholder: admin router will be imported here

__all__ = ["auth_router"]