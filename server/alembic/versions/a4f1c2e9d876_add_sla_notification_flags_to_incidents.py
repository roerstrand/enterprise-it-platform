"""add sla notification flags to incidents

Revision ID: a4f1c2e9d876
Revises: 7e2b9c4f6a1d
Create Date: 2026-08-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a4f1c2e9d876'
down_revision: Union[str, Sequence[str], None] = '7e2b9c4f6a1d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('incidents', sa.Column('sla_approaching_notified', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('incidents', sa.Column('sla_breached_notified', sa.Boolean(), server_default=sa.text('false'), nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('incidents', 'sla_breached_notified')
    op.drop_column('incidents', 'sla_approaching_notified')
