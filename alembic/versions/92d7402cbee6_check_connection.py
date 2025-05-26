"""Check connection

Revision ID: 92d7402cbee6
Revises: 05eaa420e998
Create Date: 2025-05-14 14:42:56.708894

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '92d7402cbee6'
down_revision: Union[str, None] = '05eaa420e998'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
