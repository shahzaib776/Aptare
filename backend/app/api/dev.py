from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import Settings
from app.deps import get_compiler, get_manifests, get_session, get_settings, get_store
from app.schemas.render import RenderRequest, RenderResponse
from app.schemas.template import TemplateManifest
from app.services.compile.cache import ArtifactStore
from app.services.compile.client import Compiler
from app.services.compile.pipeline import render_and_compile
from app.services.render.templates import find_template

router = APIRouter()


@router.post("/dev/render")
def dev_render(
    request: RenderRequest,
    session: Annotated[Session, Depends(get_session)],
    store: Annotated[ArtifactStore, Depends(get_store)],
    compiler: Annotated[Compiler, Depends(get_compiler)],
    manifests: Annotated[dict[str, TemplateManifest], Depends(get_manifests)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> RenderResponse:
    """Render and compile any posted resume. Developer tool: not registered in production."""
    return render_and_compile(
        session,
        store,
        compiler,
        find_template(manifests, request.template_id),
        request.resume,
        request.typography,
        request.section_order,
        request.hidden_fields,
        templates_dir=settings.templates_dir,
    )
