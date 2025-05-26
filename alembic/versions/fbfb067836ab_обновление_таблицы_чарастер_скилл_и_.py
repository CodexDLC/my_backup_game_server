"""обновление таблицы чарастер скилл и новая таблица для системы тиков

Revision ID: fbfb067836ab
Revises: e62e932594da
Create Date: 2025-05-16 00:57:42.552967

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fbfb067836ab'
down_revision: Union[str, None] = 'e62e932594da'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
