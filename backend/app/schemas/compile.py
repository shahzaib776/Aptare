from app.schemas.base import StrictModel


class Element(StrictModel):
    """A piece of resume text whose place in the PDF the compiler should find."""

    id: str
    text: str


class Placement(StrictModel):
    page: int
    rect: tuple[float, float, float, float]


class LineBox(Placement):
    chars: int


class WorkerResult(StrictModel):
    """Everything the compile worker measured, with the PDF decoded."""

    pdf: bytes
    page_count: int
    last_page_fill: float
    line_boxes: list[LineBox]
    text_map: dict[str, list[Placement]]


class CompileOutcome(StrictModel):
    """What the cache remembers about a compile (line boxes are not stored, step 9 plan)."""

    pdf_hash: str
    page_count: int
    last_page_fill: float
    text_map: dict[str, list[Placement]]
