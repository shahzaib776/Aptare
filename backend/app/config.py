from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Later files win: backend/.env overrides the repo-root .env from the README.
        env_file=("../.env", ".env"),
        extra="ignore",
    )

    env: Literal["development", "test", "production"] = "development"
    data_dir: Path = Path("./data")
    # The API runs from backend/; compose points this at the mounted templates folder.
    templates_dir: Path = Path("../templates")
    db_url: str = "sqlite:///./data/app.db"
    compiler_url: str = "http://compiler:8001"
    llm_provider: str = "none"


@lru_cache
def load_settings() -> Settings:
    return Settings()
