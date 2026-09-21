"""add_workflow_model

Revision ID: 2e33e7bfc8cb
Revises: 71143b4c04ce
Create Date: 2026-07-03 23:03:28.437480

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2e33e7bfc8cb'
down_revision: Union[str, None] = '71143b4c04ce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
