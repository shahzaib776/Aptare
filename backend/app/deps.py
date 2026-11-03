import logging
from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.config import Settings
from app.errors import AppError
from app.schemas.template import TemplateManifest
from app.services.compile.cache import ArtifactStore
from app.services.compile.client import Compiler, CompilerClient
from app.services.render.templates import ManifestError, load_manifests

logger = logging.getLogger(__name__)


def get_settings(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


def get_session(request: Request) -> Iterator[Session]:
    with request.app.state.session_factory() as session:
        yield session


def get_manifests(
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, TemplateManifest]:
    # Per request: a few small files, and a broken template fails only the request that uses it.
    try:
        return load_manifests(settings.templates_dir)
    except ManifestError as error:
        # Safe to log: it names the template and the schema problem, never resume text.
        logger.error("Broken template: %s", error)
        raise AppError("template_invalid", "A template on the server is broken.", 500) from None


def get_compiler(settings: Annotated[Settings, Depends(get_settings)]) -> Compiler:
    return CompilerClient(settings.compiler_url)


def get_store(settings: Annotated[Settings, Depends(get_settings)]) -> ArtifactStore:
    return ArtifactStore(settings.data_dir / "artifacts")
