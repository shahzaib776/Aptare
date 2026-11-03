import hashlib
import io
import zipfile

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.services.compile.cache import ArtifactStore

PDF = b"%PDF-1.7 exactly these bytes \x00\xff"


@pytest.fixture
def store(settings: Settings) -> ArtifactStore:
    return ArtifactStore(settings.data_dir / "artifacts")


def test_a_pdf_is_served_exactly_as_stored(client: TestClient, store: ArtifactStore) -> None:
    pdf_hash = store.save_pdf(PDF)

    response = client.get(f"/api/v1/files/pdf/{pdf_hash}")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content == PDF
    assert hashlib.sha256(response.content).hexdigest() == pdf_hash


@pytest.mark.parametrize("bad", ["b" * 64, "abc", "A" * 64, "a" * 65, "a.b"])
def test_an_unknown_or_malformed_pdf_hash_is_the_same_404(client: TestClient, bad: str) -> None:
    response = client.get(f"/api/v1/files/pdf/{bad}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_a_file_that_exists_under_a_malformed_hash_is_not_served(
    client: TestClient, settings: Settings
) -> None:
    """Without the hash-shape check the uppercase name would be found on disk and served."""
    folder = settings.data_dir / "artifacts" / "pdf"
    folder.mkdir(parents=True)
    (folder / f"{'A' * 64}.pdf").write_bytes(b"planted")

    assert client.get(f"/api/v1/files/pdf/{'A' * 64}").status_code == 404


def test_a_tex_without_assets_is_one_text_file(client: TestClient, store: ArtifactStore) -> None:
    tex_hash = "c" * 64
    store.save_tex(tex_hash, "\\documentclass{article}", {})

    response = client.get(f"/api/v1/files/tex/{tex_hash}")

    assert response.status_code == 200
    assert response.content == b"\\documentclass{article}"
    assert response.headers["content-type"].startswith("text/plain")
    assert 'filename="resume.tex"' in response.headers["content-disposition"]


def test_a_tex_with_assets_is_a_zip(client: TestClient, store: ArtifactStore) -> None:
    tex_hash = "d" * 64
    store.save_tex(tex_hash, "tex", {"assets/logo.png": b"png"})

    response = client.get(f"/api/v1/files/tex/{tex_hash}")

    assert response.headers["content-type"] == "application/zip"
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        assert sorted(archive.namelist()) == ["assets/logo.png", "main.tex"]
        assert archive.read("assets/logo.png") == b"png"


@pytest.mark.parametrize("bad", ["e" * 64, "short", "A" * 64])
def test_an_unknown_or_malformed_tex_hash_is_a_404(client: TestClient, bad: str) -> None:
    assert client.get(f"/api/v1/files/tex/{bad}").status_code == 404
