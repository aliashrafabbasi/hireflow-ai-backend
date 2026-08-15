"""store resume content in database

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-08-12 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, Sequence[str], None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Existing rows only reference files on the former application disk, so this
    # stays nullable for their metadata. Every new upload writes the bytes here.
    op.add_column("resumes", sa.Column("file_content", sa.LargeBinary(), nullable=True))
    op.drop_constraint("resumes_stored_filename_key", "resumes", type_="unique")
    op.drop_column("resumes", "file_path")
    op.drop_column("resumes", "stored_filename")


def downgrade() -> None:
    op.add_column("resumes", sa.Column("stored_filename", sa.String(length=255), nullable=True))
    op.add_column("resumes", sa.Column("file_path", sa.String(length=500), nullable=True))
    op.create_unique_constraint("resumes_stored_filename_key", "resumes", ["stored_filename"])
    op.drop_column("resumes", "file_content")
