from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.errors import AppError, register_error_handlers


def make_client() -> TestClient:
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/app-error")
    def app_error() -> None:
        raise AppError("provider_not_configured", "No AI provider set up.", status_code=409)

    @app.get("/detailed")
    def detailed() -> None:
        raise AppError("bad_input", "Nope.", details={"field": "email"})

    @app.get("/typed/{n}")
    def typed(n: int) -> dict[str, int]:
        return {"n": n}

    @app.get("/boom")
    def boom() -> None:
        raise RuntimeError("secret internal detail")

    return TestClient(app, raise_server_exceptions=False)


def test_app_error_uses_the_envelope_and_its_status() -> None:
    r = make_client().get("/app-error")

    assert r.status_code == 409
    assert r.json() == {
        "error": {
            "code": "provider_not_configured",
            "message": "No AI provider set up.",
            "details": None,
        }
    }


def test_app_error_details_are_passed_through() -> None:
    r = make_client().get("/detailed")

    assert r.status_code == 400
    assert r.json()["error"]["details"] == {"field": "email"}


def test_unknown_route_is_a_not_found_envelope() -> None:
    r = make_client().get("/nope")

    assert r.status_code == 404
    assert r.json()["error"]["code"] == "not_found"


def test_validation_failure_is_a_422_envelope_with_details() -> None:
    r = make_client().get("/typed/abc")

    assert r.status_code == 422
    body = r.json()["error"]
    assert body["code"] == "validation_error"
    assert body["details"]["errors"]


def test_unhandled_exception_is_a_generic_500_that_leaks_nothing() -> None:
    r = make_client().get("/boom")

    assert r.status_code == 500
    assert r.json()["error"]["code"] == "internal_error"
    assert "secret internal detail" not in r.text
