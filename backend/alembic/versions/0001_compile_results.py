"""compile results

Revision ID: 0001
Revises:
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from app.db import UuidV7

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "compile_results",
        sa.Column("id", UuidV7(), nullable=False),
        sa.Column("tex_hash", sa.String(), nullable=False),
        sa.Column("elements_hash", sa.String(), nullable=False),
        sa.Column("pdf_hash", sa.String(), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=False),
        sa.Column("last_page_fill", sa.Double(), nullable=False),
        sa.Column("text_map", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tex_hash", "elements_hash"),
    )


def downgrade() -> None:
    op.drop_table("compile_results")
