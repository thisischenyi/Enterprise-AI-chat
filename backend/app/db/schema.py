"""Database schema — User and Session SQLAlchemy models.

Uses SQLAlchemy 2 declarative mapping style with mapped_column.
Role column has CHECK constraint for ('employee', 'admin').
UUID columns use sqlalchemy UUID type (maps to PostgreSQL UUID,
SQLite uses CHAR(32) for storage compatibility).
"""

import uuid
from datetime import datetime

from sqlalchemy import String, ForeignKey, Text, Uuid
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
        # CHECK constraint enforced at DB level via Alembic migration
    )
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    token: Mapped[str] = mapped_column(String(512), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)