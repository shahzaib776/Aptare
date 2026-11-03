"""The tailored resume as JSON; the LLM fills text into these shapes and never writes LaTeX.

A TailoredResume is stored in every ResumeVersion and the submitted one never changes, so any
field added later needs a default or old rows stop loading.
"""

from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field

from app.schemas.base import StrictModel

SectionKey = Literal["experience", "projects", "education", "skills"]
LinkKind = Literal["linkedin", "github", "website", "other"]


class HeaderLink(StrictModel):
    kind: LinkKind
    label: str
    url: str


class HeaderBlock(StrictModel):
    full_name: str
    headline: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    links: list[HeaderLink] = Field(default_factory=list)


class TailoredBullet(StrictModel):
    id: UUID
    source_bullet_id: UUID
    borrowed_from_variant_id: UUID | None = None
    text: str
    stretched_terms: list[str]
    covered_keywords: list[str]
    char_budget: int | None = None
    locked: bool = False


class ExperienceItem(StrictModel):
    experience_id: UUID
    variant_id: UUID
    title: str
    company: str
    location: str | None = None
    dates: str
    bullets: list[TailoredBullet]


class ProjectItem(StrictModel):
    project_id: UUID
    name: str
    url: str | None = None
    date: str | None = None
    bullets: list[TailoredBullet]


class EducationItem(StrictModel):
    education_id: UUID
    institution: str
    degree: str
    field: str | None = None
    location: str | None = None
    dates: str | None = None
    details: list[str]


class SkillEntry(StrictModel):
    name: str
    stretched: bool


class SkillGroup(StrictModel):
    name: str
    skills: list[SkillEntry]


class SkillsItem(StrictModel):
    categories: list[SkillGroup]


class ExperienceSection(StrictModel):
    key: Literal["experience"]
    items: list[ExperienceItem]


class ProjectsSection(StrictModel):
    key: Literal["projects"]
    items: list[ProjectItem]


class EducationSection(StrictModel):
    key: Literal["education"]
    items: list[EducationItem]


class SkillsSection(StrictModel):
    key: Literal["skills"]
    items: list[SkillsItem]


Section = Annotated[
    ExperienceSection | ProjectsSection | EducationSection | SkillsSection,
    Field(discriminator="key"),
]


class TailoredResume(StrictModel):
    header: HeaderBlock
    summary: str | None = None
    sections: list[Section]
