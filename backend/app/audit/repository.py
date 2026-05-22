"""Audit repository — persists audit events with metadata-only storage.

Every safety decision (allow, block, fail_closed) generates an audit event.
Audit events contain anonymized metadata only per SAFE-06.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.schema import AuditEvent
from app.safety.scanner_interface import PolicyDecision


class AuditRepository:
    """Records and queries audit events."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record_event(
        self,
        user_id: uuid.UUID,
        model_id: str,
        source: str,
        decision: PolicyDecision,
    ) -> AuditEvent:
        """Record an audit event from a policy decision.

        Args:
            user_id: The user who triggered the scan.
            model_id: The model being used.
            source: "input" or "output".
            decision: The PolicyDecision from the safety pipeline.

        Returns:
            The persisted AuditEvent.
        """
        event = AuditEvent(
            event_id=uuid.uuid4(),
            timestamp=datetime.utcnow(),
            user_id=user_id,
            model_id=model_id,
            source=source,
            risk_categories=decision.risk_categories,
            policy_action=decision.action,
            scanner_findings=decision.scanner_findings_summary,
        )
        self._session.add(event)
        await self._session.flush()
        return event


async def get_audit_repository(session: AsyncSession) -> AuditRepository:
    """FastAPI dependency that provides an AuditRepository."""
    return AuditRepository(session)
