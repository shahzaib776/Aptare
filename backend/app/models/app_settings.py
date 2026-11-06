import uuid
from typing import Any

from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db import UuidV7, new_uuid7
from app.models.base import Base, TimestampMixin


class AppSettings(TimestampMixin, Base):
    """One row: onboarding progress and the resume defaults every new application starts from."""

    __tablename__ = "app_settings"

    id: Mapped[uuid.UUID] = mapped_column(UuidV7, primary_key=True, default=new_uuid7)
    profile_step: Mapped[str] = mapped_column(default="pending")  # pending | done | skipped
    provider_step: Mapped[str] = mapped_column(default="pending")
    resume_defaults: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
