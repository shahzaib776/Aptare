from fastapi import FastAPI

from app.api import health
from app.config import Settings, load_settings
from app.db import make_engine, make_session_factory
from app.errors import register_error_handlers

API_PREFIX = "/api/v1"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()
    app = FastAPI(title="Aptare")
    app.state.settings = settings
    app.state.session_factory = make_session_factory(make_engine(settings.db_url))
    register_error_handlers(app)
    app.include_router(health.router, prefix=API_PREFIX)
    return app
