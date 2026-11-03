from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from app.config import Settings
from app.deps import get_manifests, get_settings
from app.errors import AppError
from app.schemas.template import TemplateManifest
from app.services.render.templates import find_template

router = APIRouter()

Manifests = Annotated[dict[str, TemplateManifest], Depends(get_manifests)]


@router.get("/templates")
def list_templates(manifests: Manifests) -> list[TemplateManifest]:
    return list(manifests.values())


@router.get("/templates/{template_id}")
def get_template(template_id: str, manifests: Manifests) -> TemplateManifest:
    return find_template(manifests, template_id)


@router.get("/templates/{template_id}/preview.png")
def get_preview(
    template_id: str, manifests: Manifests, settings: Annotated[Settings, Depends(get_settings)]
) -> FileResponse:
    # The id comes from the loaded manifests, never straight from the URL, so it cannot be a path.
    manifest = find_template(manifests, template_id)
    preview = settings.templates_dir / manifest.id / "preview.png"
    if not preview.is_file():
        raise AppError("preview_not_found", "This template has no preview image.", 404)
    return FileResponse(preview, media_type="image/png")
