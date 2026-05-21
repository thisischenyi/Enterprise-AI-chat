"""Audit events — Phase 2 placeholder.

Defines audit event schema with metadata-only storage.
"""


class AuditEvent:
    """Phase 2 placeholder — audit event stub."""

    event_id: str = ""
    timestamp: str = ""
    user_id: str = ""
    risk_categories: list[str] = []
    policy_action: str = ""