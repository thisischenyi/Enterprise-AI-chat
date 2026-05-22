"""Audit query functions for admin dashboard.

Provides paginated, filtered audit event queries and statistics.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.schema import AuditEvent


class DailyCount(BaseModel):
    date: str
    count: int


class AuditStats(BaseModel):
    total_events: int
    total_blocks: int
    block_rate_percent: float
    most_active_user_id: str | None
    daily_counts_7d: list[DailyCount]


def _time_range_start(time_range: str) -> datetime:
    """Convert time_range string to a start datetime."""
    now = datetime.utcnow()
    if time_range == "7d":
        return now - timedelta(days=7)
    elif time_range == "30d":
        return now - timedelta(days=30)
    # Default "today"
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


async def list_audit_events(
    session: AsyncSession,
    time_range: str = "today",
    user_id: str | None = None,
    model_id: str | None = None,
    action: str | None = None,
    risk_category: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[AuditEvent], int]:
    """Query audit events with filters and pagination.

    Returns (events, total_count).
    """
    start = _time_range_start(time_range)

    base = select(AuditEvent).where(AuditEvent.timestamp >= start)

    if user_id:
        base = base.where(AuditEvent.user_id == user_id)
    if model_id:
        base = base.where(AuditEvent.model_id == model_id)
    if action:
        base = base.where(AuditEvent.policy_action == action)
    if risk_category:
        base = base.where(AuditEvent.risk_categories.contains(risk_category))

    # Count
    count_q = select(func.count()).select_from(base.subquery())
    total = (await session.execute(count_q)).scalar() or 0

    # Paginated results
    query = base.order_by(AuditEvent.timestamp.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(query)
    events = list(result.scalars().all())

    return events, total


async def get_audit_stats(
    session: AsyncSession,
    time_range: str = "today",
) -> AuditStats:
    """Compute audit statistics for dashboard cards."""
    start = _time_range_start(time_range)

    base = select(AuditEvent).where(AuditEvent.timestamp >= start)

    # Total events
    total_q = select(func.count()).select_from(base.subquery())
    total_events = (await session.execute(total_q)).scalar() or 0

    # Total blocks
    block_q = select(func.count()).select_from(
        base.where(AuditEvent.policy_action.in_(["block", "fail_closed"])).subquery()
    )
    total_blocks = (await session.execute(block_q)).scalar() or 0

    block_rate = (total_blocks / total_events * 100) if total_events > 0 else 0.0

    # Most active user
    user_q = (
        select(AuditEvent.user_id, func.count().label("cnt"))
        .where(AuditEvent.timestamp >= start)
        .group_by(AuditEvent.user_id)
        .order_by(func.count().desc())
        .limit(1)
    )
    user_result = await session.execute(user_q)
    row = user_result.first()
    most_active = str(row[0]) if row else None

    # Daily counts for 7-day sparkline
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    daily_counts: list[DailyCount] = []
    for i in range(7):
        day_start = (datetime.utcnow() - timedelta(days=6 - i)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        day_end = day_start + timedelta(days=1)
        day_q = select(func.count()).where(
            AuditEvent.timestamp >= day_start,
            AuditEvent.timestamp < day_end,
        )
        count = (await session.execute(day_q)).scalar() or 0
        daily_counts.append(DailyCount(date=day_start.strftime("%Y-%m-%d"), count=count))

    return AuditStats(
        total_events=total_events,
        total_blocks=total_blocks,
        block_rate_percent=round(block_rate, 1),
        most_active_user_id=most_active,
        daily_counts_7d=daily_counts,
    )
