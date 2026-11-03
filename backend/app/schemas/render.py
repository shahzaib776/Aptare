from pydantic import Field

from app.schemas.base import StrictModel
from app.schemas.compile import Placement
from app.schemas.resume import SectionKey, TailoredResume
from app.schemas.template import FieldKey
from app.schemas.typography import Typography


class RenderRequest(StrictModel):
    resume: TailoredResume
    template_id: str
    typography: Typography | None = None
    section_order: list[SectionKey] = Field(default_factory=list)
    hidden_fields: set[FieldKey] = Field(default_factory=set)


class RenderResponse(StrictModel):
    tex_hash: str
    pdf_hash: str
    page_count: int
    last_page_fill: float
    text_map: dict[str, list[Placement]]
