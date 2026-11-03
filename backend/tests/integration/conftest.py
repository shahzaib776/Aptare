from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.deps import get_compiler
from app.main import create_app
from app.models.base import Base
from tests.fakes import FakeCompiler


@pytest.fixture
def compiler() -> FakeCompiler:
    return FakeCompiler()


@pytest.fixture
def make_client(compiler: FakeCompiler) -> Callable[[Settings], TestClient]:
    def build(settings: Settings) -> TestClient:
        app = create_app(settings)
        Base.metadata.create_all(app.state.session_factory.kw["bind"])
        app.dependency_overrides[get_compiler] = lambda: compiler
        return TestClient(app)

    return build


@pytest.fixture
def client(settings: Settings, make_client: Callable[[Settings], TestClient]) -> TestClient:
    return make_client(settings)
