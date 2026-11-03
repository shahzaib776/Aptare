from typing import Annotated

from fastapi import APIRouter, Depends, Response
from fastapi.responses import FileResponse

from app.deps import get_store
from app.errors import AppError
from app.services.compile.cache import ArtifactStore

router = APIRouter()

Store = Annotated[ArtifactStore, Depends(get_store)]

# A hash names its content forever, so browsers may keep it.
_IMMUTABLE = {"Cache-Control": "private, max-age=31536000, immutable"}


def _not_found() -> AppError:
    return AppError("not_found", "Not found.", 404)


@router.get("/files/pdf/{pdf_hash}")
def get_pdf(pdf_hash: str, store: Store) -> FileResponse:
    """The cached PDF, served exactly as stored (EX-2); never recompiles (rule 7)."""
    path = store.pdf_path(pdf_hash)
    if path is None:
        raise _not_found()
    return FileResponse(
        path,
        media_type="application/pdf",
        filename="resume.pdf",
        content_disposition_type="inline",
        headers=_IMMUTABLE,
    )


@router.get("/files/tex/{tex_hash}")
def get_tex(tex_hash: str, store: Store) -> Response:
    """The `.tex`, or a zip when the template has assets."""
    download = store.tex_download(tex_hash)
    if download is None:
        raise _not_found()
    return Response(
        download.data,
        media_type=download.media_type,
        headers={
            **_IMMUTABLE,
            "Content-Disposition": f'attachment; filename="{download.filename}"',
        },
    )
