"""backfill match checked_by from resume uploader

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-07-31 16:45:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Attribute historical matches to the account that uploaded the resume
    # (n8n / staff login). Industry-standard: every action has an actor.
    op.execute(
        sa.text(
            """
            UPDATE match_results AS mr
            SET
                checked_by_id = r.user_id,
                checked_at = COALESCE(mr.checked_at, mr.created_at)
            FROM resumes AS r
            WHERE mr.resume_id = r.id
              AND mr.checked_by_id IS NULL
            """
        )
    )


def downgrade() -> None:
    # Do not clear attribution on downgrade — data loss for audit trail.
    pass
