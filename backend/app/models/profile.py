import uuid

from sqlalchemy import JSON, CheckConstraint, ForeignKey, LargeBinary, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import UuidV7, new_uuid7
from app.models.base import Base, TimestampMixin

# Dates are "YYYY-MM" strings: they sort correctly and need no invented day. The schemas
# validate the format at the API boundary.


def _fk(target: str) -> Mapped[uuid.UUID]:
    return mapped_column(UuidV7, ForeignKey(target, ondelete="CASCADE"))


class Profile(TimestampMixin, Base):
    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(UuidV7, primary_key=True, default=new_uuid7)
    full_name: Mapped[str]
    headline: Mapped[str | None]
    email: Mapped[str | None]
    phone: Mapped[str | None]
    location: Mapped[str | None]
    summary: Mapped[str | None] = mapped_column(Text)
    links: Mapped[list[dict[str, str]]] = mapped_column(JSON, default=list)


class Experience(TimestampMixin, Base):
    __tablename__ = "experiences"

    id: Mapped[uuid.UUID] = mapped_column(UuidV7, primary_key=True, default=new_uuid7)
    profile_id: Mapped[uuid.UUID] = _fk("profiles.id")
    company: Mapped[str]
    location: Mapped[str | None]
    start_date: Mapped[str] = mapped_column(String(7))
    end_date: Mapped[str | None] = mapped_column(String(7))  # None means present
    sort_order: Mapped[int] = mapped_column(default=0)


class Variant(TimestampMixin, Base):
    """A title held in an experience."""

    __tablename__ = "variants"

    id: Mapped[uuid.UUID] = mapped_column(UuidV7, primary_key=True, default=new_uuid7)
    experience_id: Mapped[uuid.UUID] = _fk("experiences.id")
    title: Mapped[str]
    sort_order: Mapped[int] = mapped_column(default=0)


class Project(TimestampMixin, Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(UuidV7, primary_key=True, default=new_uuid7)
    profile_id: Mapped[uuid.UUID] = _fk("profiles.id")
    name: Mapped[str]
    url: Mapped[str | None]
    date: Mapped[str | None] = mapped_column(String(7))
    sort_order: Mapped[int] = mapped_column(default=0)


class Bullet(TimestampMixin, Base):
    """Owned by an experience or a project. Two real foreign keys, not an owner_type/owner_id
    pair, so deleting the owner deletes its bullets in the database itself."""

    __tablename__ = "bullets"
    __table_args__ = (
        CheckConstraint(
            "(experience_id IS NULL) != (project_id IS NULL)", name="bullet_has_exactly_one_owner"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UuidV7, primary_key=True, default=new_uuid7)
    experience_id: Mapped[uuid.UUID | None] = mapped_column(
        UuidV7, ForeignKey("experiences.id", ondelete="CASCADE")
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UuidV7, ForeignKey("projects.id", ondelete="CASCADE")
    )
    text: Mapped[str] = mapped_column(Text)
    skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    pinned: Mapped[bool] = mapped_column(default=False)
    sort_order: Mapped[int] = mapped_column(default=0)
    embedding: Mapped[bytes | None] = mapped_column(LargeBinary)


class BulletVariant(Base):
    """ "Also use for": which titles a bullet may appear under."""

    __tablename__ = "bullet_variants"

    bullet_id: Mapped[uuid.UUID] = mapped_column(
        UuidV7, ForeignKey("bullets.id", ondelete="CASCADE"), primary_key=True
    )
    variant_id: Mapped[uuid.UUID] = mapped_column(
        UuidV7, ForeignKey("variants.id", ondelete="CASCADE"), primary_key=True
    )


class Education(TimestampMixin, Base):
    __tablename__ = "education"

    id: Mapped[uuid.UUID] = mapped_column(UuidV7, primary_key=True, default=new_uuid7)
    profile_id: Mapped[uuid.UUID] = _fk("profiles.id")
    institution: Mapped[str]
    degree: Mapped[str]
    field: Mapped[str | None]
    location: Mapped[str | None]
    start_date: Mapped[str | None] = mapped_column(String(7))
    end_date: Mapped[str | None] = mapped_column(String(7))
    details: Mapped[list[str]] = mapped_column(JSON, default=list)


class SkillCategory(TimestampMixin, Base):
    __tablename__ = "skill_categories"

    id: Mapped[uuid.UUID] = mapped_column(UuidV7, primary_key=True, default=new_uuid7)
    profile_id: Mapped[uuid.UUID] = _fk("profiles.id")
    name: Mapped[str]
    skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    sort_order: Mapped[int] = mapped_column(default=0)


__all__ = [
    "Bullet",
    "BulletVariant",
    "Education",
    "Experience",
    "Profile",
    "Project",
    "SkillCategory",
    "Variant",
]
