"""Admin API routes — admin-only endpoints with role enforcement.

Admin endpoints require Depends(get_admin_user) which checks user.role == "admin"
and raises 403 for non-admin users (per AUTH-03 and threat model T-01-04, T-01-10).
403 response contains only generic "Admin access required" message — no user
identity or role enumeration hints (per T-01-10).
"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.audit_queries import (
    AuditStats,
    list_audit_events,
    get_audit_stats,
)
from app.audit.events import AuditEventResponse
from app.auth.current_user import get_admin_user
from app.db import get_db_session
from app.db.schema import User

router = APIRouter()


class PaginatedAuditResponse(BaseModel):
    events: list[AuditEventResponse]
    total: int
    page: int
    page_size: int


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


@router.get("/audit", response_model=PaginatedAuditResponse)
async def get_audit_events(
    time_range: str = Query("today", pattern="^(today|7d|30d)$"),
    user_id: str | None = Query(None),
    model_id: str | None = Query(None),
    action: str | None = Query(None),
    risk_category: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session),
) -> PaginatedAuditResponse:
    """Paginated audit events with multi-dimension filters."""
    events, total = await list_audit_events(
        session=db,
        time_range=time_range,
        user_id=user_id,
        model_id=model_id,
        action=action,
        risk_category=risk_category,
        page=page,
        page_size=page_size,
    )
    return PaginatedAuditResponse(
        events=[AuditEventResponse.model_validate(e) for e in events],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/audit/stats", response_model=AuditStats)
async def get_audit_statistics(
    time_range: str = Query("today", pattern="^(today|7d|30d)$"),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session),
) -> AuditStats:
    """Audit statistics for dashboard cards."""
    return await get_audit_stats(session=db, time_range=time_range)
