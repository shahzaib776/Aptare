from pathlib import Path

from sqlalchemy.orm import Session

from app.schemas.render import RenderResponse
from app.schemas.resume import SectionKey, TailoredResume
from app.schemas.template import FieldKey, TemplateManifest
from app.schemas.typography import Typography
from app.services.compile.cache import ArtifactStore, compile_cached
from app.services.compile.client import Compiler
from app.services.render.layout import check_layout
from app.services.render.renderer import render


def render_and_compile(
    session: Session,
    store: ArtifactStore,
    compiler: Compiler,
    manifest: TemplateManifest,
    resume: TailoredResume,
    typography: Typography | None,
    section_order: list[SectionKey],
    hidden_fields: set[FieldKey],
    *,
    templates_dir: Path,
) -> RenderResponse:
    """Check the layout, render the `.tex`, and compile it unless the same input already was."""
    typography = typography or manifest.typography_defaults
    check_layout(manifest, typography, section_order)
    bundle = render(
        resume, manifest, typography, section_order, hidden_fields, templates_dir=templates_dir
    )
    outcome = compile_cached(session, store, compiler, bundle, templates_dir / manifest.id)
    return RenderResponse(tex_hash=bundle.tex_hash, **outcome.model_dump())
