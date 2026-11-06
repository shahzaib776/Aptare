"""profile, experiences, titles, bullets, projects, education, skills and app settings

Revision ID: 0002
Revises: 0001
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from app.db import UuidV7

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "app_settings",
        sa.Column("id", UuidV7(), nullable=False),
        sa.Column("profile_step", sa.String(), nullable=False),
        sa.Column("provider_step", sa.String(), nullable=False),
        sa.Column("resume_defaults", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "profiles",
        sa.Column("id", UuidV7(), nullable=False),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("headline", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("links", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "education",
        sa.Column("id", UuidV7(), nullable=False),
        sa.Column("profile_id", UuidV7(), nullable=False),
        sa.Column("institution", sa.String(), nullable=False),
        sa.Column("degree", sa.String(), nullable=False),
        sa.Column("field", sa.String(), nullable=True),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("start_date", sa.String(length=7), nullable=True),
        sa.Column("end_date", sa.String(length=7), nullable=True),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "experiences",
        sa.Column("id", UuidV7(), nullable=False),
        sa.Column("profile_id", UuidV7(), nullable=False),
        sa.Column("company", sa.String(), nullable=False),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("start_date", sa.String(length=7), nullable=False),
        sa.Column("end_date", sa.String(length=7), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "projects",
        sa.Column("id", UuidV7(), nullable=False),
        sa.Column("profile_id", UuidV7(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("url", sa.String(), nullable=True),
        sa.Column("date", sa.String(length=7), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "skill_categories",
        sa.Column("id", UuidV7(), nullable=False),
        sa.Column("profile_id", UuidV7(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("skills", sa.JSON(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "bullets",
        sa.Column("id", UuidV7(), nullable=False),
        sa.Column("experience_id", UuidV7(), nullable=True),
        sa.Column("project_id", UuidV7(), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("skills", sa.JSON(), nullable=False),
        sa.Column("pinned", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("embedding", sa.LargeBinary(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "(experience_id IS NULL) != (project_id IS NULL)", name="bullet_has_exactly_one_owner"
        ),
        sa.ForeignKeyConstraint(["experience_id"], ["experiences.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "variants",
        sa.Column("id", UuidV7(), nullable=False),
        sa.Column("experience_id", UuidV7(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["experience_id"], ["experiences.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "bullet_variants",
        sa.Column("bullet_id", UuidV7(), nullable=False),
        sa.Column("variant_id", UuidV7(), nullable=False),
        sa.ForeignKeyConstraint(["bullet_id"], ["bullets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["variant_id"], ["variants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("bullet_id", "variant_id"),
    )


def downgrade() -> None:
    op.drop_table("bullet_variants")
    op.drop_table("variants")
    op.drop_table("bullets")
    op.drop_table("skill_categories")
    op.drop_table("projects")
    op.drop_table("experiences")
    op.drop_table("education")
    op.drop_table("profiles")
    op.drop_table("app_settings")
