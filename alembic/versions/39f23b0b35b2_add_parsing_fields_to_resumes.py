"""add parsing fields to resumes

Revision ID: 39f23b0b35b2
Revises: 3a0de48945a1
Create Date: 2026-07-29

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "39f23b0b35b2"
down_revision: Union[str, Sequence[str], None] = "3a0de48945a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "resumes",
        sa.Column(
            "extracted_text",
            sa.Text(),
            nullable=True,
        ),
    )

    op.add_column(
        "resumes",
        sa.Column(
            "processing_status",
            sa.String(length=30),
            nullable=False,
            server_default="pending",
        ),
    )

    op.add_column(
        "resumes",
        sa.Column(
            "parsed_at",
            sa.DateTime(),
            nullable=True,
        ),
    )

    # Remove default for future inserts
    op.alter_column(
        "resumes",
        "processing_status",
        server_default=None,
    )


def downgrade() -> None:
    op.drop_column("resumes", "parsed_at")
    op.drop_column("resumes", "processing_status")
    op.drop_column("resumes", "extracted_text")