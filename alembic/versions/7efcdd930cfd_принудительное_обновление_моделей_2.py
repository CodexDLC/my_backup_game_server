"""Принудительное обновление моделей 2

Revision ID: 7efcdd930cfd
Revises: 4246ea03388c
Create Date: 2025-05-16 01:18:01.139039

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7efcdd930cfd'
down_revision: Union[str, None] = '4246ea03388c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
