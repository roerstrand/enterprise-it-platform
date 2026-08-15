"""add role to users

Revision ID: f3a1c9d2e7b4
Revises: 06480d97028c
Create Date: 2026-08-15 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f3a1c9d2e7b4'
down_revision: Union[str, Sequence[str], None] = '06480d97028c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('role', sa.String(), nullable=False, server_default='viewer'))
    # Bootstrap: befintlig lägsta user-id (om någon finns) blir admin så att RBAC går att logga in och testa
    # utan manuell SQL. Nya installationer utan users påverkas inte.
    op.execute(
        "UPDATE users SET role = 'admin' WHERE id = (SELECT MIN(id) FROM users)"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'role')
