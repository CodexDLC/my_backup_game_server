"""Удаление столбца created_at из character_status

Revision ID: fca04092273f
Revises: b60df4c2468a
Create Date: 2025-05-12 15:44:41.448013

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fca04092273f'
down_revision: Union[str, None] = 'b60df4c2468a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
