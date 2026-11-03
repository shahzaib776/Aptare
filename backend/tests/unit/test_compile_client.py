import base64
import json
import logging
from typing import Any

import httpx
import pytest

from app.errors import AppError
from app.schemas.compile import Element
from app.services.compile.client import CompilerClient

SECRET = "SECRET-RESUME-TEXT"
PDF = b"%PDF-1.7 fake"
REPLY: dict[str, Any] = {
    "pdf": base64.b64encode(PDF).decode(),
    "page_count": 1,
    "last_page_fill": 0.4,
    "line_boxes": [{"page": 0, "rect": [1, 2, 3, 4], "chars": 12}],
    "text_map": {"b1": [{"page": 0, "rect": [10, 20, 30, 40]}]},
}


def client_for(handler: Any) -> CompilerClient:
    return CompilerClient("http://compiler:8001", transport=httpx.MockTransport(handler))


def envelope(code: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"error": {"code": code, "message": "m", "details": details or {}}}


def compile_with(client: CompilerClient) -> None:
    client.compile(SECRET, {}, [Element(id="b1", text=SECRET)])


def test_the_request_carries_tex_assets_and_elements() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=REPLY)

    client_for(handler).compile("tex", {"assets/a.png": b"png"}, [Element(id="b1", text="Hi")])

    assert seen[0].url == "http://compiler:8001/compile"
    assert json.loads(seen[0].content) == {
        "tex": "tex",
        "assets": {"assets/a.png": base64.b64encode(b"png").decode()},
        "elements": [{"id": "b1", "text": "Hi"}],
    }


def test_the_reply_is_parsed() -> None:
    result = client_for(lambda r: httpx.Response(200, json=REPLY)).compile("t", {}, [])

    assert result.pdf == PDF
    assert result.page_count == 1
    assert result.last_page_fill == 0.4
    assert result.line_boxes[0].chars == 12
    assert result.text_map["b1"][0].rect == (10, 20, 30, 40)


@pytest.mark.parametrize(
    ("status", "worker_code", "code", "http_status"),
    [
        (422, "compile_failed", "compile_failed", 422),
        (408, "compile_timeout", "compile_timeout", 504),
        (503, "compiler_not_ready", "compiler_unavailable", 503),
        (422, "invalid_request", "compiler_error", 502),
        (500, "internal_error", "compiler_error", 502),
    ],
)
def test_worker_errors_become_api_errors(
    status: int, worker_code: str, code: str, http_status: int
) -> None:
    client = client_for(lambda r: httpx.Response(status, json=envelope(worker_code)))

    with pytest.raises(AppError) as raised:
        compile_with(client)

    assert (raised.value.code, raised.value.status_code) == (code, http_status)


def test_a_compile_failure_keeps_the_log_tail_for_the_caller() -> None:
    body = envelope("compile_failed", {"log_tail": "! Undefined control sequence."})
    client = client_for(lambda r: httpx.Response(422, json=body))

    with pytest.raises(AppError) as raised:
        compile_with(client)

    assert raised.value.details == {"log_tail": "! Undefined control sequence."}


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(200, text="not json"),
        httpx.Response(200, json={"pdf": "x"}),
        httpx.Response(200, json={**REPLY, "pdf": "***not base64***"}),
        httpx.Response(502, text="<html>bad gateway</html>"),
        httpx.Response(500, json={"unexpected": True}),
    ],
)
def test_a_reply_we_do_not_understand_is_a_compiler_error(response: httpx.Response) -> None:
    with pytest.raises(AppError) as raised:
        compile_with(client_for(lambda r: response))

    assert (raised.value.code, raised.value.status_code) == ("compiler_error", 502)


@pytest.mark.parametrize("failure", [httpx.ConnectError("refused"), httpx.ReadTimeout("slow")])
def test_an_unreachable_worker_is_unavailable(failure: httpx.HTTPError) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise failure

    with pytest.raises(AppError) as raised:
        compile_with(client_for(handler))

    assert (raised.value.code, raised.value.status_code) == ("compiler_unavailable", 503)


def test_nothing_from_the_resume_or_the_log_is_logged(caplog: pytest.LogCaptureFixture) -> None:
    body = envelope("compile_failed", {"log_tail": SECRET + "-LOG"})
    client = client_for(lambda r: httpx.Response(422, json=body))

    with caplog.at_level(logging.DEBUG), pytest.raises(AppError):
        compile_with(client)

    assert SECRET not in caplog.text


@pytest.mark.parametrize(
    ("status", "worker_code", "words"),
    [
        (408, "compile_timeout", "too long"),
        (503, "compiler_not_ready", "not ready"),
        (422, "compile_failed", "did not compile"),
    ],
)
def test_each_error_says_what_actually_happened(status: int, worker_code: str, words: str) -> None:
    client = client_for(lambda r: httpx.Response(status, json=envelope(worker_code)))

    with pytest.raises(AppError) as raised:
        compile_with(client)

    assert words in raised.value.message
