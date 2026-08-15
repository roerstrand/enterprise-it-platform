"""add unique constraint to users.email

Revision ID: 9d4b2f7c1e6a
Revises: 1a9f6c3e8b2d
Create Date: 2026-08-15 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '9d4b2f7c1e6a'
down_revision: Union[str, Sequence[str], None] = '1a9f6c3e8b2d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Login matchar på email (get_user_by_email_from_db) - utan denna constraint kan två
    # konton dela email och vilket konto som faktiskt loggas in på blir odefinierat.
    op.create_unique_constraint('uq_users_email', 'users', ['email'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uq_users_email', 'users', type_='unique')
