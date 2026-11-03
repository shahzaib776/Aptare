from typing import Literal, Self

from pydantic import Field, model_validator

from app.schemas.base import StrictModel
from app.schemas.resume import SectionKey
from app.schemas.typography import Typography

FieldKey = Literal[
    "headline",
    "email",
    "phone",
    "location",
    "summary",
    "linkedin",
    "github",
    "website",
    "other",
]


class SectionSpec(StrictModel):
    key: SectionKey
    column: Literal["main", "side"]
    movable: bool
    required: bool


class TemplateManifest(StrictModel):
    # The id becomes a folder name and a URL segment, so it can never hold a path.
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]*$")
    name: str = Field(min_length=1)
    license: str = Field(min_length=1)
    fields: set[FieldKey]
    sections: list[SectionSpec]
    typography_defaults: Typography
    typography_bounds: dict[str, tuple[float, float]]

    @model_validator(mode="after")
    def _check_sections_and_bounds(self) -> Self:
        keys = [section.key for section in self.sections]
        if len(keys) != len(set(keys)):
            raise ValueError("section keys must be unique")

        controls = set(Typography.model_fields)
        if set(self.typography_bounds) != controls:
            raise ValueError(f"typography_bounds must cover exactly {sorted(controls)}")

        for name, (low, high) in self.typography_bounds.items():
            default = getattr(self.typography_defaults, name)
            if not low <= default <= high:
                raise ValueError(f"{name}: default {default} is outside its bounds [{low}, {high}]")
        return self
