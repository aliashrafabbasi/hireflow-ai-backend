"""add candidate_name to resumes

Revision ID: a1b2c3d4e5f6
Revises: 752fd753808d
Create Date: 2026-07-31 01:45:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "752fd753808d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "resumes",
        sa.Column("candidate_name", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("resumes", "candidate_name")
