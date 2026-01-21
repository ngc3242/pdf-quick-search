"""add user approval fields

Revision ID: 5f2cd4f23956
Revises: add_original_text
Create Date: 2026-01-22 00:23:07.896046

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5f2cd4f23956'
down_revision = 'add_original_text'
branch_labels = None
depends_on = None


def upgrade():
    # Add approval fields to users table
    with op.batch_alter_table('users', schema=None) as batch_op:
        # Add approval_status with server_default='approved' for existing users
        batch_op.add_column(sa.Column(
            'approval_status', 
            sa.String(length=20), 
            nullable=False, 
            server_default='approved'
        ))
        batch_op.add_column(sa.Column('approved_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('approved_by_id', sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column('approval_reason', sa.Text(), nullable=True))
        batch_op.create_index(batch_op.f('ix_users_approval_status'), ['approval_status'], unique=False)
        batch_op.create_foreign_key('fk_users_approved_by', 'users', ['approved_by_id'], ['id'])

    # Remove server_default after existing rows are updated
    # Keep 'approved' as the default in the model, but remove from DB level
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('approval_status', server_default=None)


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_constraint('fk_users_approved_by', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_users_approval_status'))
        batch_op.drop_column('approval_reason')
        batch_op.drop_column('approved_by_id')
        batch_op.drop_column('approved_at')
        batch_op.drop_column('approval_status')
