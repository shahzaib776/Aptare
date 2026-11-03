import base64
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.pdfs import make_pdf
from worker import main
from worker.errors import CompileFailedError, CompileTimeoutError
from worker.main import create_app

SECRET = "SECRET-RESUME-TEXT"


@pytest.fixture
def calls(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, dict[str, bytes]]]:
    seen: list[tuple[str, dict[str, bytes]]] = []

    def fake_compile(tex: str, assets: dict[str, bytes]) -> bytes:
        seen.append((tex, assets))
        return make_pdf([["Built a multi-", "threaded crawler"]])

    monkeypatch.setattr(main, "compile_tex", fake_compile)
    return seen


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(create_app()) as c:
        yield c


def body(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {"tex": "\\documentclass{article}", "assets": {}, "elements": []}
    data.update(overrides)
    return data


def b64(data: bytes) -> str:
    return base64.b64encode(data).decode()


def test_compile_returns_pdf_and_measurements(
    client: TestClient, calls: list[tuple[str, dict[str, bytes]]]
) -> None:
    response = client.post(
        "/compile",
        json=body(
            assets={"logo.png": b64(b"png-bytes")},
            elements=[{"id": "b1", "text": "Built a multi-threaded crawler"}],
        ),
    )
    assert response.status_code == 200
    data = response.json()
    assert base64.b64decode(data["pdf"]).startswith(b"%PDF")
    assert data["page_count"] == 1
    assert 0 < data["last_page_fill"] < 1
    assert len(data["line_boxes"]) == 2
    assert len(data["text_map"]["b1"]) == 2
    assert calls == [("\\documentclass{article}", {"logo.png": b"png-bytes"})]


@pytest.mark.parametrize(
    "path",
    ["../escape.tex", "/etc/passwd", "a/../../b.png", ".hidden", "a//b.png", "main.tex", "a b.png"],
)
def test_unsafe_asset_paths_are_rejected_before_compiling(
    client: TestClient, calls: list[tuple[str, dict[str, bytes]]], path: str
) -> None:
    response = client.post("/compile", json=body(assets={path: b64(b"x")}))
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_request"
    assert calls == []


def test_asset_that_is_not_base64_is_rejected(
    client: TestClient, calls: list[tuple[str, dict[str, bytes]]]
) -> None:
    response = client.post("/compile", json=body(assets={"a.png": "not base64!!"}))
    assert response.status_code == 422
    assert calls == []


def test_oversized_tex_is_rejected(
    client: TestClient, calls: list[tuple[str, dict[str, bytes]]]
) -> None:
    response = client.post("/compile", json=body(tex="x" * 1_000_001))
    assert response.status_code == 422
    assert calls == []


def test_validation_errors_do_not_echo_the_request(
    client: TestClient, calls: list[tuple[str, dict[str, bytes]]]
) -> None:
    response = client.post("/compile", json=body(tex=SECRET, assets={"../x": b64(b"x")}))
    assert response.status_code == 422
    assert SECRET not in response.text


def test_unknown_fields_are_rejected(
    client: TestClient, calls: list[tuple[str, dict[str, bytes]]]
) -> None:
    assert client.post("/compile", json=body(extra=1)).status_code == 422


def test_compile_failure_is_an_envelope_with_the_log_tail(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def boom(tex: str, assets: dict[str, bytes]) -> bytes:
        raise CompileFailedError("! Undefined control sequence.")

    monkeypatch.setattr(main, "compile_tex", boom)
    response = client.post("/compile", json=body())
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "compile_failed"
    assert error["details"]["log_tail"] == "! Undefined control sequence."


def test_compile_timeout_is_408(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    def slow(tex: str, assets: dict[str, bytes]) -> bytes:
        raise CompileTimeoutError

    monkeypatch.setattr(main, "compile_tex", slow)
    response = client.post("/compile", json=body())
    assert response.status_code == 408
    assert response.json()["error"]["code"] == "compile_timeout"


def test_health_is_ok_when_tectonic_is_ready(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(main, "is_ready", lambda: True)
    assert client.get("/health").status_code == 200


def test_health_is_503_when_tectonic_is_not_ready(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(main, "is_ready", lambda: False)
    response = client.get("/health")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "compiler_not_ready"


def test_unexpected_errors_still_use_the_envelope(monkeypatch: pytest.MonkeyPatch) -> None:
    def broken(tex: str, assets: dict[str, bytes]) -> bytes:
        raise RuntimeError(SECRET)

    monkeypatch.setattr(main, "compile_tex", broken)
    with TestClient(create_app(), raise_server_exceptions=False) as client:
        response = client.post("/compile", json=body())
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "internal_error"
    assert SECRET not in response.text
