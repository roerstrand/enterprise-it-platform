"""create incident_change_links table

Revision ID: 7e2b9c4f6a1d
Revises: c3f8a1d5b7e2
Create Date: 2026-08-16 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7e2b9c4f6a1d'
down_revision: Union[str, Sequence[str], None] = 'c3f8a1d5b7e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'incident_change_links',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('incident_id', sa.Integer(), sa.ForeignKey('incidents.id'), nullable=False),
        # Inget FK mot changes.id - den tabellen ägs av ChangeService (C#/EF Core), inte denna alembic-historik
        sa.Column('change_id', sa.Integer(), nullable=False),
        sa.Column('linked_by_user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('incident_id', 'change_id', name='uq_incident_change_link'),
    )
    op.create_index('ix_incident_change_links_incident_id', 'incident_change_links', ['incident_id'])
    op.create_index('ix_incident_change_links_change_id', 'incident_change_links', ['change_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_incident_change_links_change_id', table_name='incident_change_links')
    op.drop_index('ix_incident_change_links_incident_id', table_name='incident_change_links')
    op.drop_table('incident_change_links')
