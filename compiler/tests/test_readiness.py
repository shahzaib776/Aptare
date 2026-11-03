import pytest

from worker import run_tectonic


def test_not_ready_when_the_binary_is_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(run_tectonic, "TECTONIC", "/nonexistent/tectonic")
    assert run_tectonic.is_ready() is False


@pytest.mark.compile
def test_ready_in_the_image() -> None:
    assert run_tectonic.is_ready() is True
