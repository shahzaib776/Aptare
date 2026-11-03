from collections.abc import Generator
from types import SimpleNamespace
from typing import cast

from fastapi import Request

from app.deps import get_session


class SpySession:
    def __init__(self) -> None:
        self.closed = False

    def __enter__(self) -> "SpySession":
        return self

    def __exit__(self, *exc: object) -> None:
        self.closed = True


def request_with(sessions: list[SpySession]) -> Request:
    factory = lambda: sessions.pop(0)  # noqa: E731
    stub = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(session_factory=factory)))
    return cast(Request, stub)


def test_each_request_gets_its_own_session_and_it_is_closed_afterwards() -> None:
    first, second = SpySession(), SpySession()
    request = request_with([first, second])

    generator = cast(Generator[object, None, None], get_session(request))
    assert next(generator) is first
    assert not first.closed
    generator.close()

    assert first.closed
    assert next(cast(Generator[object, None, None], get_session(request))) is second
