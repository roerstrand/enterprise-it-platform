"""add assignee and SLA tracking fields to incidents

Revision ID: c3f8a1d5b7e2
Revises: 9d4b2f7c1e6a
Create Date: 2026-08-16 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3f8a1d5b7e2'
down_revision: Union[str, Sequence[str], None] = '9d4b2f7c1e6a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('incidents', sa.Column('assignee_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True))
    op.add_column('incidents', sa.Column('first_response_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('incidents', sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True))
    op.create_index('ix_incidents_assignee_user_id', 'incidents', ['assignee_user_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_incidents_assignee_user_id', table_name='incidents')
    op.drop_column('incidents', 'resolved_at')
    op.drop_column('incidents', 'first_response_at')
    op.drop_column('incidents', 'assignee_user_id')
