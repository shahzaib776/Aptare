import re
from typing import Annotated, Self

from pydantic import (
    AfterValidator,
    Base64Bytes,
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

MAX_TEX_CHARS = 1_000_000
MAX_ASSETS = 50
MAX_ASSET_BYTES = 5_000_000
MAX_TOTAL_ASSET_BYTES = 20_000_000
MAX_ELEMENTS = 1_000
MAX_ELEMENT_CHARS = 5_000

# Rule 12: assets are written into the compile directory, so every path segment must be a plain
# name. A leading letter or digit rules out "..", "." and hidden files; no leading slash.
ASSET_PATH = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*(/[A-Za-z0-9][A-Za-z0-9._-]*)*")
RESERVED_PATHS = {"main.tex"}


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Element(Strict):
    id: str = Field(min_length=1, max_length=100)
    text: str = Field(max_length=MAX_ELEMENT_CHARS)


class Placement(Strict):
    page: int
    rect: tuple[float, float, float, float]


class LineBox(Placement):
    chars: int


def _check_asset_path(path: str) -> str:
    if ASSET_PATH.fullmatch(path) is None or path in RESERVED_PATHS:
        raise ValueError("asset path must be a plain relative path")
    return path


class CompileRequest(Strict):
    tex: str = Field(max_length=MAX_TEX_CHARS)
    assets: dict[Annotated[str, AfterValidator(_check_asset_path)], Base64Bytes] = Field(
        default_factory=dict, max_length=MAX_ASSETS
    )
    elements: list[Element] = Field(default_factory=list, max_length=MAX_ELEMENTS)

    @model_validator(mode="after")
    def _check_asset_sizes(self) -> Self:
        sizes = [len(data) for data in self.assets.values()]
        if sizes and (max(sizes) > MAX_ASSET_BYTES or sum(sizes) > MAX_TOTAL_ASSET_BYTES):
            raise ValueError("assets are too large")
        return self


class CompileResponse(Strict):
    pdf: str  # base64
    page_count: int
    last_page_fill: float
    line_boxes: list[LineBox]
    text_map: dict[str, list[Placement]]
