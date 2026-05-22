"""Audit events — Pydantic models for API serialization.

Separate from SQLAlchemy model in db/schema.py.
Contains metadata only — never raw prompts, outputs, or PII values.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class AuditEventResponse(BaseModel):
    """Pydantic model for audit event API responses."""

    event_id: uuid.UUID
    timestamp: datetime
    user_id: uuid.UUID
    model_id: str
    source: str
    risk_categories: list[str]
    policy_action: str
    scanner_findings: dict

    model_config = {"from_attributes": True}
