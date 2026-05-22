"""002 — Create audit_events table.

For future PostgreSQL production use. MVP uses Base.metadata.create_all.

Revision ID: 002
Create Date: 2026-05-22
"""

from alembic import op
import sqlalchemy as sa


revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_events",
        sa.Column("event_id", sa.Uuid(), primary_key=True),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("model_id", sa.String(100), nullable=False),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("risk_categories", sa.JSON(), nullable=False),
        sa.Column("policy_action", sa.String(20), nullable=False),
        sa.Column("scanner_findings", sa.JSON(), nullable=False),
    )
    op.create_index("ix_audit_events_user_timestamp", "audit_events", ["user_id", "timestamp"])
    op.create_index("ix_audit_events_action_timestamp", "audit_events", ["policy_action", "timestamp"])


def downgrade() -> None:
    op.drop_index("ix_audit_events_action_timestamp", table_name="audit_events")
    op.drop_index("ix_audit_events_user_timestamp", table_name="audit_events")
    op.drop_table("audit_events")
