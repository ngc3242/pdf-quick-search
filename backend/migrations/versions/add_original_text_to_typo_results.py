"""add original_text column to typo_check_results

Revision ID: add_original_text
Revises: add_system_prompt_configs
Create Date: 2026-01-16

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "add_original_text"
down_revision = "add_system_prompt_configs"
branch_labels = None
depends_on = None


def upgrade():
    # Add original_text column with default empty string
    op.add_column(
        "typo_check_results",
        sa.Column("original_text", sa.Text(), nullable=False, server_default=""),
    )


def downgrade():
    op.drop_column("typo_check_results", "original_text")
