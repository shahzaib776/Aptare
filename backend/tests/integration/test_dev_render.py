import hashlib
from collections.abc import Callable
from typing import Any

from fastapi.testclient import TestClient

from app.config import Settings
from tests.fakes import FakeCompiler
from tests.resumes import full_resume_data


def payload(**changes: Any) -> dict[str, Any]:
    return {"resume": full_resume_data(), "template_id": "dense-single", **changes}


def test_render_returns_hashes_and_the_text_map(client: TestClient) -> None:
    response = client.post("/api/v1/dev/render", json=payload())

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"tex_hash", "pdf_hash", "page_count", "last_page_fill", "text_map"}
    assert len(body["tex_hash"]) == len(body["pdf_hash"]) == 64
    assert "summary" in body["text_map"]


def test_the_rendered_pdf_downloads_byte_identical_to_its_hash(client: TestClient) -> None:
    """EX-2: the preview and the download are the same bytes."""
    pdf_hash = client.post("/api/v1/dev/render", json=payload()).json()["pdf_hash"]

    download = client.get(f"/api/v1/files/pdf/{pdf_hash}")

    assert hashlib.sha256(download.content).hexdigest() == pdf_hash


def test_the_tex_is_downloadable_by_its_hash(client: TestClient) -> None:
    tex_hash = client.post("/api/v1/dev/render", json=payload()).json()["tex_hash"]

    download = client.get(f"/api/v1/files/tex/{tex_hash}")

    assert download.status_code == 200
    assert b"Ada Lovelace" in download.content


def test_a_second_identical_render_does_not_call_the_compiler(
    client: TestClient, compiler: FakeCompiler
) -> None:
    first = client.post("/api/v1/dev/render", json=payload()).json()
    second = client.post("/api/v1/dev/render", json=payload()).json()

    assert first == second
    assert len(compiler.calls) == 1


def test_layout_choices_reach_the_tex(client: TestClient, compiler: FakeCompiler) -> None:
    layout = {"section_order": ["projects", "experience"], "hidden_fields": ["summary"]}

    client.post("/api/v1/dev/render", json=payload(**layout))

    tex = compiler.calls[0].tex
    assert "Summary" not in tex
    assert tex.index("Projects") < tex.index("Experience")


def test_custom_typography_reaches_the_tex(client: TestClient, compiler: FakeCompiler) -> None:
    typography = {
        "base_font_pt": 9.0,
        "line_spread": 1.0,
        "margin_in": 0.5,
        "item_sep_pt": 2.0,
        "section_sep_pt": 6.0,
    }

    client.post("/api/v1/dev/render", json=payload(typography=typography))

    assert "margin=0.5in" in compiler.calls[0].tex
    assert r"\fontsize{9.0}" in compiler.calls[0].tex


def test_typography_outside_the_template_bounds_is_a_422(
    client: TestClient, compiler: FakeCompiler
) -> None:
    typography = {
        "base_font_pt": 20.0,
        "line_spread": 1.0,
        "margin_in": 0.5,
        "item_sep_pt": 2.0,
        "section_sep_pt": 6.0,
    }

    response = client.post("/api/v1/dev/render", json=payload(typography=typography))

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "typography_out_of_bounds"
    assert compiler.calls == []


def test_a_repeated_section_is_a_422(client: TestClient) -> None:
    response = client.post("/api/v1/dev/render", json=payload(section_order=["skills", "skills"]))

    assert response.json()["error"]["code"] == "invalid_section_order"


def test_an_unknown_template_is_a_404(client: TestClient) -> None:
    response = client.post("/api/v1/dev/render", json=payload(template_id="nope"))

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "template_not_found"


def test_a_worker_failure_comes_back_as_the_error_envelope(
    client: TestClient, compiler: FakeCompiler
) -> None:
    from app.errors import AppError

    compiler.error = AppError(
        "compile_failed", "The resume did not compile.", 422, {"log_tail": "x"}
    )

    response = client.post("/api/v1/dev/render", json=payload())

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "compile_failed"


def test_an_invalid_resume_is_a_validation_error(client: TestClient) -> None:
    response = client.post(
        "/api/v1/dev/render", json={"resume": {"header": {}}, "template_id": "dense-single"}
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_the_dev_endpoint_does_not_exist_in_production(
    settings: Settings, make_client: Callable[[Settings], TestClient]
) -> None:
    production = make_client(settings.model_copy(update={"env": "production"}))

    response = production.post("/api/v1/dev/render", json=payload())

    assert response.status_code == 404
