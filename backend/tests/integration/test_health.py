import httpx
from fastapi.testclient import TestClient

from app.api.health import compiler_reachable
from app.config import Settings
from app.main import create_app


def test_health_reports_unreachable_compiler(settings: Settings) -> None:
    client = TestClient(create_app(settings))

    r = client.get("/api/v1/health")

    assert r.status_code == 200
    assert r.json() == {"status": "ok", "compiler": "unreachable"}


def test_probe_is_ok_when_the_compiler_answers_healthy() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={"status": "ok"}))

    assert compiler_reachable("http://compiler:8001", transport=transport) is True


def test_probe_is_not_ok_on_a_server_error() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(503))

    assert compiler_reachable("http://compiler:8001", transport=transport) is False


def test_probe_is_not_ok_when_the_connection_fails() -> None:
    def refuse(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused")

    assert (
        compiler_reachable("http://compiler:8001", transport=httpx.MockTransport(refuse)) is False
    )
