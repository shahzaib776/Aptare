import uuid
from typing import Any

from sqlalchemy import JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import UuidV7, new_uuid7
from app.models.base import Base, TimestampMixin


class CompileResult(TimestampMixin, Base):
    """What one compile produced, remembered so the same input never compiles twice."""

    __tablename__ = "compile_results"
    # The text map's ids are bullet ids that are not in the .tex, so the key needs both.
    __table_args__ = (UniqueConstraint("tex_hash", "elements_hash"),)

    id: Mapped[uuid.UUID] = mapped_column(UuidV7, primary_key=True, default=new_uuid7)
    tex_hash: Mapped[str]
    elements_hash: Mapped[str]
    pdf_hash: Mapped[str]
    page_count: Mapped[int]
    last_page_fill: Mapped[float]
    text_map: Mapped[dict[str, Any]] = mapped_column(JSON)
