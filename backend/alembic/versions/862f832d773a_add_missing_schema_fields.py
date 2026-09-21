"""Add missing schema fields

Revision ID: 862f832d773a
Revises: c4b88ed4d1cb
Create Date: 2026-07-03 21:04:46.385186

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '862f832d773a'
down_revision: Union[str, None] = 'c4b88ed4d1cb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
