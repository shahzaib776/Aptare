import hashlib
import json
import os
import re
import tempfile
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.compile_result import CompileResult
from app.schemas.compile import CompileOutcome, Element
from app.services.compile.client import Compiler
from app.services.compile.elements import elements_from
from app.services.render.renderer import TexBundle

# Hashes arrive from URLs in step 10; only this shape may ever become part of a file path.
_HASH = re.compile(r"[0-9a-f]{64}")


def _write_atomically(path: Path, data: bytes) -> None:
    """Write beside the target, then rename, so a reader never sees half a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
        os.replace(temp, path)
    except BaseException:
        Path(temp).unlink(missing_ok=True)
        raise


class ArtifactStore:
    """PDFs and tex bundles on disk, addressed by hash (rule 7)."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def save_pdf(self, pdf: bytes) -> str:
        pdf_hash = hashlib.sha256(pdf).hexdigest()
        _write_atomically(self.root / "pdf" / f"{pdf_hash}.pdf", pdf)
        return pdf_hash

    def pdf_path(self, pdf_hash: str) -> Path | None:
        """The stored file, or None when the hash is malformed or nothing is stored under it."""
        if not _HASH.fullmatch(pdf_hash):
            return None
        path = self.root / "pdf" / f"{pdf_hash}.pdf"
        return path if path.is_file() else None

    def save_tex(self, tex_hash: str, tex: str, assets: dict[str, bytes]) -> Path:
        # Asset names come from our own template folders; user-uploaded templates (TP-9) must
        # be checked where they are uploaded.
        if not _HASH.fullmatch(tex_hash):
            raise ValueError("malformed tex hash")
        folder = self.root / "tex" / tex_hash
        _write_atomically(folder / "main.tex", tex.encode("utf-8"))
        for name, data in assets.items():
            _write_atomically(folder / name, data)
        return folder


def compile_cached(
    session: Session,
    store: ArtifactStore,
    compiler: Compiler,
    bundle: TexBundle,
    template_folder: Path,
) -> CompileOutcome:
    """Compile `bundle` unless the same tex and elements were compiled before (EX-2)."""
    elements = elements_from(bundle.visible)
    elements_hash = _hash_elements(elements)
    row = _lookup(session, bundle.tex_hash, elements_hash)
    if row and store.pdf_path(row.pdf_hash):
        return _outcome(row)

    assets = {a.relative_to(template_folder).as_posix(): a.read_bytes() for a in bundle.assets}
    result = compiler.compile(bundle.tex, assets, elements)
    pdf_hash = store.save_pdf(result.pdf)
    store.save_tex(bundle.tex_hash, bundle.tex, assets)

    # A row whose PDF file vanished is refreshed in place instead of inserted again.
    row = row or CompileResult(tex_hash=bundle.tex_hash, elements_hash=elements_hash)
    row.pdf_hash = pdf_hash
    row.page_count = result.page_count
    row.last_page_fill = result.last_page_fill
    row.text_map = {k: [p.model_dump() for p in v] for k, v in result.text_map.items()}
    session.add(row)
    try:
        session.commit()
    except IntegrityError:
        # An identical request finished first. Compiles are deterministic, so its row is ours.
        session.rollback()
        existing = _lookup(session, bundle.tex_hash, elements_hash)
        if existing is None:
            raise
        return _outcome(existing)
    return _outcome(row)


def _hash_elements(elements: list[Element]) -> str:
    canonical = json.dumps([e.model_dump() for e in elements], separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _lookup(session: Session, tex_hash: str, elements_hash: str) -> CompileResult | None:
    return session.scalars(
        select(CompileResult).where(
            CompileResult.tex_hash == tex_hash, CompileResult.elements_hash == elements_hash
        )
    ).one_or_none()


def _outcome(row: CompileResult) -> CompileOutcome:
    return CompileOutcome(
        pdf_hash=row.pdf_hash,
        page_count=row.page_count,
        last_page_fill=row.last_page_fill,
        text_map=row.text_map,
    )
