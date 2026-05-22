"""Add model_configs and policy_configs tables.

Revision ID: 004_model_policy
"""

from alembic import op
import sqlalchemy as sa

revision = "004_model_policy"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "model_configs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("provider_type", sa.String(50), nullable=False),
        sa.Column("endpoint_url", sa.String(500), nullable=False),
        sa.Column("api_key_encrypted", sa.String(500), nullable=False),
        sa.Column("model_id", sa.String(100), unique=True, nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "policy_configs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("scanner_name", sa.String(100), unique=True, nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("sensitivity", sa.String(20), nullable=False, server_default="medium"),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("policy_configs")
    op.drop_table("model_configs")
