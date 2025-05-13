"""Удаление столбца created_at из character_status

Revision ID: b60df4c2468a
Revises: 4c409397301a
Create Date: 2025-05-12 15:41:47.888789

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b60df4c2468a'
down_revision: Union[str, None] = '4c409397301a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Удаление столбца created_at из таблицы character_status
    op.drop_column('character_status', 'created_at')

def downgrade() -> None:
    """Downgrade schema."""
    # Восстановление столбца created_at в таблице character_status
    op.add_column('character_status', sa.Column('created_at', sa.DateTime(), nullable=True))