"""add system prompt configs table

Revision ID: add_system_prompt_configs
Revises: 684a1bd2d6af
Create Date: 2026-01-15 16:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "add_system_prompt_configs"
down_revision = "684a1bd2d6af"
branch_labels = None
depends_on = None


def upgrade():
    """Create system_prompt_configs table."""
    op.create_table(
        "system_prompt_configs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider"),
    )
    op.create_index(
        op.f("ix_system_prompt_configs_provider"),
        "system_prompt_configs",
        ["provider"],
        unique=True,
    )


def downgrade():
    """Drop system_prompt_configs table."""
    op.drop_index(
        op.f("ix_system_prompt_configs_provider"), table_name="system_prompt_configs"
    )
    op.drop_table("system_prompt_configs")
