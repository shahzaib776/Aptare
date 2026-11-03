import uuid
from pathlib import Path
from typing import Any

import uuid_utils
from sqlalchemy import Engine, String, create_engine
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine import Dialect, make_url
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.types import TypeDecorator, TypeEngine


def new_uuid7() -> uuid.UUID:
    return uuid.UUID(str(uuid_utils.uuid7()))


class UuidV7(TypeDecorator[uuid.UUID]):
    """UUID column: a 36-char string in SQLite, a native UUID in Postgres."""

    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect: Dialect) -> TypeEngine[Any]:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(postgresql.UUID(as_uuid=True))
        return dialect.type_descriptor(String(36))

    def process_bind_param(self, value: uuid.UUID | str | None, dialect: Dialect) -> Any:
        if value is None:
            return None
        parsed = value if isinstance(value, uuid.UUID) else uuid.UUID(value)
        return parsed if dialect.name == "postgresql" else str(parsed)

    def process_result_value(self, value: Any, dialect: Dialect) -> uuid.UUID | None:
        if value is None:
            return None
        return value if isinstance(value, uuid.UUID) else uuid.UUID(value)


def make_engine(url: str) -> Engine:
    parsed = make_url(url)
    if parsed.get_backend_name() != "sqlite":
        return create_engine(url)

    # FastAPI runs sync routes in a thread pool, so SQLite connections must cross threads.
    if parsed.database in (None, "", ":memory:"):
        return create_engine(url, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    # A missing parent directory otherwise surfaces as an opaque "unable to open database file".
    Path(parsed.database).parent.mkdir(parents=True, exist_ok=True)
    return create_engine(url, connect_args={"check_same_thread": False})


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(engine, expire_on_commit=False)
