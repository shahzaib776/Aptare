import logging
import shutil
from collections.abc import Callable
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings

PNG = b"\x89PNG\r\n\x1a\n"


def test_the_list_has_every_template(client: TestClient) -> None:
    response = client.get("/api/v1/templates")

    assert response.status_code == 200
    assert [t["id"] for t in response.json()] == ["dense-single"]


def test_one_template_returns_its_manifest(client: TestClient) -> None:
    body = client.get("/api/v1/templates/dense-single").json()

    assert body["name"] and body["typography_bounds"]["base_font_pt"] == [8.5, 11.0]


def test_an_unknown_template_is_a_404_envelope(client: TestClient) -> None:
    response = client.get("/api/v1/templates/nope")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "template_not_found"


def test_the_preview_is_a_png(client: TestClient) -> None:
    response = client.get("/api/v1/templates/dense-single/preview.png")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content.startswith(PNG)


def test_a_template_without_a_preview_is_a_404(
    settings: Settings, make_client: Callable[[Settings], TestClient], tmp_path: Path
) -> None:
    copy = tmp_path / "templates"
    shutil.copytree(settings.templates_dir, copy)
    (copy / "dense-single" / "preview.png").unlink(missing_ok=True)

    response = make_client(settings.model_copy(update={"templates_dir": copy})).get(
        "/api/v1/templates/dense-single/preview.png"
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "preview_not_found"


def test_a_broken_template_is_an_error_envelope_and_the_log_names_it(
    settings: Settings,
    make_client: Callable[[Settings], TestClient],
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    copy = tmp_path / "templates"
    shutil.copytree(settings.templates_dir, copy)
    (copy / "broken").mkdir()
    (copy / "broken" / "manifest.json").write_text("{not json", encoding="utf-8")
    client = make_client(settings.model_copy(update={"templates_dir": copy}))

    with caplog.at_level(logging.ERROR):
        response = client.get("/api/v1/templates")

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "template_invalid"
    assert "broken" in caplog.text
