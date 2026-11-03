import hashlib
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.schemas.resume import SectionKey, TailoredResume
from app.schemas.template import FieldKey, SectionSpec, TemplateManifest
from app.schemas.typography import Typography
from app.services.render.escape import escape_resume
from app.services.render.jinja_env import make_environment

_environment = lru_cache(make_environment)


@dataclass(frozen=True)
class TexBundle:
    tex: str
    assets: list[Path]
    tex_hash: str


def order_sections(specs: list[SectionSpec], section_order: list[SectionKey]) -> list[SectionKey]:
    """Section keys in render order: main column first, then side; nothing leaves its column."""
    rank = {key: position for position, key in enumerate(section_order)}
    ordered: list[SectionKey] = []
    for column in ("main", "side"):
        in_column = [spec for spec in specs if spec.column == column]
        # A stable sort keeps manifest order for sections the caller did not mention.
        movable = iter(
            sorted(
                (spec.key for spec in in_column if spec.movable),
                key=lambda key: rank.get(key, len(rank)),
            )
        )
        ordered += [next(movable) if spec.movable else spec.key for spec in in_column]
    return ordered


def render(
    resume: TailoredResume,
    manifest: TemplateManifest,
    typography: Typography,
    section_order: list[SectionKey],
    hidden_fields: set[FieldKey],
    *,
    templates_dir: Path,
) -> TexBundle:
    """Fill the template with the resume's visible parts; the same input gives the same bytes."""
    visible = _visible_parts(resume, manifest, section_order, hidden_fields)
    template = _environment(templates_dir).get_template(f"{manifest.id}/template.tex.j2")
    # TP-6: the only place text is escaped, after hiding and before the template sees it.
    tex = template.render(resume=escape_resume(visible), typography=typography)

    folder = templates_dir / manifest.id
    assets = sorted(p for p in (folder / "assets").rglob("*") if p.is_file())
    return TexBundle(tex=tex, assets=assets, tex_hash=_hash(tex, assets, folder))


def _visible_parts(
    resume: TailoredResume,
    manifest: TemplateManifest,
    section_order: list[SectionKey],
    hidden_fields: set[FieldKey],
) -> TailoredResume:
    """TP-3 and TP-5: keep only declared, unhidden fields and sections, in order."""
    shown = manifest.fields - hidden_fields
    header = resume.header
    scalars = {
        name: getattr(header, name) if name in shown else None
        for name in ("headline", "email", "phone", "location")
    }
    links = [link for link in header.links if link.kind in shown]
    keys = order_sections(manifest.sections, section_order)
    return resume.model_copy(
        update={
            "header": header.model_copy(update={**scalars, "links": links}),
            "summary": resume.summary if "summary" in shown else None,
            "sections": [s for key in keys for s in resume.sections if s.key == key],
        }
    )


def _hash(tex: str, assets: list[Path], folder: Path) -> str:
    """The compile-cache key: a changed template asset must also change it."""
    digest = hashlib.sha256()

    def feed(data: bytes) -> None:
        # Length-prefixed so the boundary between parts can never be faked by their content.
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)

    feed(tex.encode("utf-8"))
    for asset in assets:
        feed(asset.relative_to(folder).as_posix().encode("utf-8"))
        feed(asset.read_bytes())
    return digest.hexdigest()
