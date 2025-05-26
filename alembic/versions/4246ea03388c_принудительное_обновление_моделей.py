"""Принудительное обновление моделей

Revision ID: 4246ea03388c
Revises: fbfb067836ab
Create Date: 2025-05-16 01:07:39.823977

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4246ea03388c'
down_revision: Union[str, None] = 'fbfb067836ab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
