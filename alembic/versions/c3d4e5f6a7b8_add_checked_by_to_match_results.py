"""add checked_by to match_results

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-07-31 15:20:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "match_results",
        sa.Column("checked_by_id", sa.UUID(), nullable=True),
    )
    op.add_column(
        "match_results",
        sa.Column("checked_at", sa.DateTime(), nullable=True),
    )
    op.create_foreign_key(
        "fk_match_results_checked_by_id_users",
        "match_results",
        "users",
        ["checked_by_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_match_results_checked_by_id",
        "match_results",
        ["checked_by_id"],
    )
    # Backfill checked_at from created_at for existing rows
    op.execute(
        sa.text(
            "UPDATE match_results SET checked_at = created_at "
            "WHERE checked_at IS NULL"
        )
    )


def downgrade() -> None:
    op.drop_index("ix_match_results_checked_by_id", table_name="match_results")
    op.drop_constraint(
        "fk_match_results_checked_by_id_users",
        "match_results",
        type_="foreignkey",
    )
    op.drop_column("match_results", "checked_at")
    op.drop_column("match_results", "checked_by_id")
