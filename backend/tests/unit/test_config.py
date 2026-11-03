from pathlib import Path

import pytest
from pydantic import ValidationError

from app.config import Settings


def test_defaults_work_without_any_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("ENV", "DATA_DIR", "DB_URL", "COMPILER_URL", "LLM_PROVIDER"):
        monkeypatch.delenv(name, raising=False)

    s = Settings()

    assert s.env == "development"
    assert s.data_dir == Path("./data")
    assert s.db_url.startswith("sqlite:///")
    assert s.llm_provider == "none"


def test_environment_variables_override_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COMPILER_URL", "http://compiler:9000")
    monkeypatch.setenv("ENV", "production")

    s = Settings()

    assert s.compiler_url == "http://compiler:9000"
    assert s.env == "production"


def test_unknown_env_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENV", "staging-ish")

    with pytest.raises(ValidationError):
        Settings()
