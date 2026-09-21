"""add composite index

Revision ID: c4b88ed4d1cb
Revises: f1e88ed4d1ca
Create Date: 2026-07-03 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c4b88ed4d1cb'
down_revision = 'f1e88ed4d1ca'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create composite index to optimize claim_next_job SELECT FOR UPDATE SKIP LOCKED
    op.create_index(
        'ix_jobs_claiming_composite',
        'jobs',
        ['status', 'run_at', 'queue_id'],
        unique=False
    )

def downgrade() -> None:
    op.drop_index('ix_jobs_claiming_composite', table_name='jobs')
