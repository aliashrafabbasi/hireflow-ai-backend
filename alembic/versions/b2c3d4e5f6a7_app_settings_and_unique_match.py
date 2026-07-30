"""app settings + unique match resume/job

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-31 02:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "app_settings",
        sa.Column("key", sa.String(length=100), primary_key=True),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    # Seed default threshold
    op.execute(
        sa.text(
            "INSERT INTO app_settings (key, value, updated_at) "
            "VALUES ('match_score_threshold', '50', NOW()) "
            "ON CONFLICT (key) DO NOTHING"
        )
    )

    # Deduplicate match_results keeping newest row per resume_id+job_id
    op.execute(
        sa.text(
            """
            DELETE FROM match_results
            WHERE id NOT IN (
                SELECT DISTINCT ON (resume_id, job_id) id
                FROM match_results
                ORDER BY resume_id, job_id, created_at DESC
            )
            """
        )
    )

    op.create_index(
        "uq_match_results_resume_job",
        "match_results",
        ["resume_id", "job_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_match_results_resume_job", table_name="match_results")
    op.drop_table("app_settings")
