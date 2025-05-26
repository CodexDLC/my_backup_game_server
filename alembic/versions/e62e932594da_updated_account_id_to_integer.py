"""Updated account_id to INTEGER

Revision ID: e62e932594da
Revises: 92d7402cbee6
Create Date: 2025-05-14 15:24:30.488257

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e62e932594da'
down_revision: Union[str, None] = '92d7402cbee6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
