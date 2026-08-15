"""add timestamps to incidents and incident_updates, author to incident_updates

Revision ID: b7c2e4f9a1d6
Revises: f3a1c9d2e7b4
Create Date: 2026-08-15 09:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7c2e4f9a1d6'
down_revision: Union[str, Sequence[str], None] = 'f3a1c9d2e7b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('incidents', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.add_column('incidents', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.add_column('incident_updates', sa.Column('author_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True))
    op.add_column('incident_updates', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('incident_updates', 'created_at')
    op.drop_column('incident_updates', 'author_user_id')
    op.drop_column('incidents', 'updated_at')
    op.drop_column('incidents', 'created_at')
