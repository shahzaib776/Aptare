import hashlib
from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from app.db import make_engine, make_session_factory
from app.errors import AppError
from app.models.base import Base
from app.models.compile_result import CompileResult
from app.schemas.resume import TailoredResume
from app.services.compile.cache import ArtifactStore, compile_cached
from app.services.compile.elements import elements_from
from app.services.render.renderer import TexBundle, render
from app.services.render.templates import load_manifests
from tests.fakes import FakeCompiler
from tests.resumes import bullet, full_resume, full_resume_data

TEMPLATES = Path(__file__).resolve().parents[3] / "templates"
FOLDER = TEMPLATES / "dense-single"


@pytest.fixture
def factory() -> sessionmaker[Session]:
    engine = make_engine("sqlite://")
    Base.metadata.create_all(engine)
    return make_session_factory(engine)


@pytest.fixture
def session(factory: sessionmaker[Session]) -> Iterator[Session]:
    with factory() as session:
        yield session


@pytest.fixture
def store(tmp_path: Path) -> ArtifactStore:
    return ArtifactStore(tmp_path / "artifacts")


def bundle_of(resume: TailoredResume) -> TexBundle:
    manifest = load_manifests(TEMPLATES)["dense-single"]
    return render(
        resume, manifest, manifest.typography_defaults, [], set(), templates_dir=TEMPLATES
    )


def rows(session: Session) -> int:
    return session.scalar(select(func.count()).select_from(CompileResult)) or 0


def test_the_first_compile_calls_the_worker_and_stores_everything(
    session: Session, store: ArtifactStore
) -> None:
    compiler = FakeCompiler()
    bundle = bundle_of(full_resume())

    outcome = compile_cached(session, store, compiler, bundle, FOLDER)

    assert len(compiler.calls) == 1
    assert compiler.calls[0].tex == bundle.tex
    assert compiler.calls[0].elements == elements_from(bundle.visible)
    pdf = b"%PDF-fake " + bundle.tex.encode()
    assert outcome.pdf_hash == hashlib.sha256(pdf).hexdigest()
    stored = store.pdf_path(outcome.pdf_hash)
    assert stored is not None and stored.read_bytes() == pdf
    assert (store.save_tex(bundle.tex_hash, bundle.tex, {}) / "main.tex").read_text() == bundle.tex
    assert rows(session) == 1


def test_the_same_input_twice_compiles_once(session: Session, store: ArtifactStore) -> None:
    compiler = FakeCompiler()
    bundle = bundle_of(full_resume())

    first = compile_cached(session, store, compiler, bundle, FOLDER)
    second = compile_cached(session, store, compiler, bundle, FOLDER)

    assert len(compiler.calls) == 1
    assert second == first


def test_same_text_with_different_bullet_ids_gets_its_own_text_map(
    session: Session, store: ArtifactStore
) -> None:
    compiler = FakeCompiler()
    data = full_resume_data()
    data["sections"][1]["items"][0]["bullets"] = [bullet(500, "Cut costs by $5k")]
    other = TailoredResume.model_validate(data)
    first_bundle, other_bundle = bundle_of(full_resume()), bundle_of(other)
    assert first_bundle.tex_hash == other_bundle.tex_hash

    first = compile_cached(session, store, compiler, first_bundle, FOLDER)
    second = compile_cached(session, store, compiler, other_bundle, FOLDER)

    assert len(compiler.calls) == 2
    assert first.pdf_hash == second.pdf_hash
    assert set(first.text_map) != set(second.text_map)
    assert rows(session) == 2
    assert len(list((store.root / "pdf").iterdir())) == 1


def test_a_missing_pdf_file_is_recompiled(session: Session, store: ArtifactStore) -> None:
    compiler = FakeCompiler()
    bundle = bundle_of(full_resume())
    outcome = compile_cached(session, store, compiler, bundle, FOLDER)
    path = store.pdf_path(outcome.pdf_hash)
    assert path is not None
    path.unlink()

    again = compile_cached(session, store, compiler, bundle, FOLDER)

    assert len(compiler.calls) == 2
    assert again == outcome
    assert store.pdf_path(outcome.pdf_hash) is not None
    assert rows(session) == 1


def test_a_compile_that_fails_stores_nothing(session: Session, store: ArtifactStore) -> None:
    compiler = FakeCompiler()
    compiler.error = AppError("compile_failed", "no", 422)

    with pytest.raises(AppError):
        compile_cached(session, store, compiler, bundle_of(full_resume()), FOLDER)

    assert rows(session) == 0
    assert not (store.root / "pdf").exists()


def test_two_identical_requests_at_once_both_succeed(
    session: Session, store: ArtifactStore, factory: sessionmaker[Session]
) -> None:
    other_compiler = FakeCompiler()
    compiler = FakeCompiler()
    bundle = bundle_of(full_resume())

    def other_request_finishes_first() -> None:
        with factory() as other:
            compile_cached(other, store, other_compiler, bundle, FOLDER)

    compiler.during_compile = other_request_finishes_first

    outcome = compile_cached(session, store, compiler, bundle, FOLDER)

    assert outcome.pdf_hash == hashlib.sha256(b"%PDF-fake " + bundle.tex.encode()).hexdigest()
    assert rows(session) == 1


def test_template_assets_are_sent_by_path_relative_to_the_template(
    session: Session, store: ArtifactStore, tmp_path: Path
) -> None:
    folder = tmp_path / "tpl"
    (folder / "assets").mkdir(parents=True)
    logo = folder / "assets" / "logo.png"
    logo.write_bytes(b"png")
    real = bundle_of(full_resume())
    bundle = TexBundle(real.tex, [logo], real.tex_hash, real.visible)
    compiler = FakeCompiler()

    compile_cached(session, store, compiler, bundle, folder)

    assert compiler.calls[0].assets == {"assets/logo.png": b"png"}
    assert (store.root / "tex" / bundle.tex_hash / "assets" / "logo.png").read_bytes() == b"png"
