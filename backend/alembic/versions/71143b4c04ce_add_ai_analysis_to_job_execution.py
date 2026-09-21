"""add_ai_analysis_to_job_execution

Revision ID: 71143b4c04ce
Revises: 862f832d773a
Create Date: 2026-07-03 22:56:00.100643

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '71143b4c04ce'
down_revision: Union[str, None] = '862f832d773a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
