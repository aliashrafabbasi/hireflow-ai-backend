"""add match indexes for foreign keys

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-08-21 04:00:00.000000
"""

from typing import Sequence, Union

from alembic import op

revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, Sequence[str], None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_resume_skills_resume_id",
        "resume_skills",
        ["resume_id"],
        unique=False,
    )
    op.create_index(
        "ix_job_skills_job_id",
        "job_skills",
        ["job_id"],
        unique=False,
    )
    op.create_index(
        "ix_match_results_job_id",
        "match_results",
        ["job_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_match_results_job_id", table_name="match_results")
    op.drop_index("ix_job_skills_job_id", table_name="job_skills")
    op.drop_index("ix_resume_skills_resume_id", table_name="resume_skills")
