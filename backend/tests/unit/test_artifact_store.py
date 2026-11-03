import hashlib
from pathlib import Path

import pytest

from app.services.compile.cache import ArtifactStore

PDF = b"%PDF-1.7 some bytes"
TEX_HASH = "a" * 64


@pytest.fixture
def store(tmp_path: Path) -> ArtifactStore:
    return ArtifactStore(tmp_path / "artifacts")


def test_save_pdf_returns_the_sha256_and_stores_the_exact_bytes(
    store: ArtifactStore, tmp_path: Path
) -> None:
    pdf_hash = store.save_pdf(PDF)

    assert pdf_hash == hashlib.sha256(PDF).hexdigest()
    assert (tmp_path / "artifacts" / "pdf" / f"{pdf_hash}.pdf").read_bytes() == PDF


def test_saving_the_same_pdf_twice_is_harmless(store: ArtifactStore, tmp_path: Path) -> None:
    first = store.save_pdf(PDF)
    second = store.save_pdf(PDF)

    assert first == second
    assert [p.name for p in (tmp_path / "artifacts" / "pdf").iterdir()] == [f"{first}.pdf"]


def test_pdf_path_finds_a_saved_pdf(store: ArtifactStore) -> None:
    pdf_hash = store.save_pdf(PDF)

    path = store.pdf_path(pdf_hash)

    assert path is not None and path.read_bytes() == PDF


def test_pdf_path_is_none_for_an_unknown_hash(store: ArtifactStore) -> None:
    assert store.pdf_path("b" * 64) is None


@pytest.mark.parametrize(
    "bad",
    ["", "abc", "../../etc/passwd", "A" * 64, "g" * 64, "a" * 63, "a" * 65, "a/" + "b" * 62],
)
def test_pdf_path_never_builds_a_path_from_a_malformed_hash(store: ArtifactStore, bad: str) -> None:
    assert store.pdf_path(bad) is None


def test_save_tex_writes_the_document_and_its_assets(store: ArtifactStore, tmp_path: Path) -> None:
    folder = store.save_tex(TEX_HASH, "\\documentclass{article}", {"assets/logo.png": b"png"})

    assert folder == tmp_path / "artifacts" / "tex" / TEX_HASH
    assert (folder / "main.tex").read_text(encoding="utf-8") == "\\documentclass{article}"
    assert (folder / "assets" / "logo.png").read_bytes() == b"png"


def test_save_tex_twice_is_harmless(store: ArtifactStore) -> None:
    store.save_tex(TEX_HASH, "a", {})
    folder = store.save_tex(TEX_HASH, "a", {})

    assert (folder / "main.tex").read_text(encoding="utf-8") == "a"


def test_save_tex_rejects_a_malformed_hash(store: ArtifactStore) -> None:
    with pytest.raises(ValueError, match="hash"):
        store.save_tex("../escape", "a", {})


def test_a_failed_write_leaves_no_temp_file_and_no_pdf(
    store: ArtifactStore, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken_replace(src: str, dst: Path) -> None:
        raise OSError("disk full")

    monkeypatch.setattr("app.services.compile.cache.os.replace", broken_replace)

    with pytest.raises(OSError, match="disk full"):
        store.save_pdf(PDF)

    assert list((tmp_path / "artifacts" / "pdf").iterdir()) == []


def test_pdf_path_refuses_files_that_exist_but_are_not_addressed_by_a_valid_hash(
    store: ArtifactStore, tmp_path: Path
) -> None:
    """Without the shape check both would be served: a file one folder up, an uppercase name."""
    root = tmp_path / "artifacts"
    (root / "pdf").mkdir(parents=True)
    (root / "secret.pdf").write_bytes(b"not an artifact")
    (root / "pdf" / f"{'A' * 64}.pdf").write_bytes(b"wrong case")

    assert store.pdf_path("../secret") is None
    assert store.pdf_path("A" * 64) is None
