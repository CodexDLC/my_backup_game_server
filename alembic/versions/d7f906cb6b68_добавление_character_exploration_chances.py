"""Добавление character_exploration_chances

Revision ID: d7f906cb6b68
Revises: 602cc08e4a24
Create Date: 2025-05-16 01:27:31.874888

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd7f906cb6b68'
down_revision: Union[str, None] = '602cc08e4a24'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
