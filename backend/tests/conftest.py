from pathlib import Path

import pytest

from app.config import Settings


@pytest.fixture(autouse=True)
def _no_dotenv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Settings reads ./.env; running from an empty directory keeps a developer's real .env out.
    monkeypatch.chdir(tmp_path)


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        env="test",
        data_dir=tmp_path,
        db_url="sqlite://",
        compiler_url="http://127.0.0.1:1",
    )
