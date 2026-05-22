"""Database schema — User and Session SQLAlchemy models.

Uses SQLAlchemy 2 declarative mapping style with mapped_column.
MVP uses SQLite (aiosqlite); production can switch to PostgreSQL (asyncpg).
UUID columns use sqlalchemy Uuid type (CHAR(32) storage in SQLite,
native UUID in PostgreSQL when switched).
"""

import uuid
from datetime import datetime

from sqlalchemy import Index, JSON, String, ForeignKey, Text, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    token: Mapped[str] = mapped_column(String(512), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)


class AuditEvent(Base):
    __tablename__ = "audit_events"
    __table_args__ = (
        Index("ix_audit_events_user_timestamp", "user_id", "timestamp"),
        Index("ix_audit_events_action_timestamp", "policy_action", "timestamp"),
    )

    event_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    timestamp: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    model_id: Mapped[str] = mapped_column(String(100), nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    risk_categories: Mapped[list] = mapped_column(JSON, nullable=False)
    policy_action: Mapped[str] = mapped_column(String(20), nullable=False)
    scanner_findings: Mapped[dict] = mapped_column(JSON, nullable=False)