import time
import uuid
from pathlib import Path

import pytest
from sqlalchemy import ForeignKey, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from app.config import Settings
from app.db import UuidV7, make_engine, make_session_factory, new_uuid7
from app.models.base import TimestampMixin


class ScratchBase(DeclarativeBase):
    """Test-only registry, so these tables never leak into the app's real Base.metadata."""


class Widget(TimestampMixin, ScratchBase):
    __tablename__ = "widgets_test"

    id: Mapped[uuid.UUID] = mapped_column(UuidV7, primary_key=True, default=new_uuid7)
    name: Mapped[str]


class Parent(ScratchBase):
    __tablename__ = "parents_test"

    id: Mapped[int] = mapped_column(primary_key=True)


class Child(ScratchBase):
    __tablename__ = "children_test"

    id: Mapped[int] = mapped_column(primary_key=True)
    parent_id: Mapped[int] = mapped_column(ForeignKey("parents_test.id"))


def make_session(url: str) -> Session:
    engine = make_engine(url)
    ScratchBase.metadata.create_all(engine)
    return make_session_factory(engine)()


def test_uuid_column_round_trips_a_real_uuid(settings: Settings) -> None:
    with make_session(settings.db_url) as session:
        widget = Widget(name="a")
        session.add(widget)
        session.commit()
        stored_id = widget.id

        loaded = session.scalars(select(Widget)).one()

    assert isinstance(loaded.id, uuid.UUID)
    assert loaded.id == stored_id
    assert loaded.id.version == 7


def test_timestamps_are_set_on_insert(settings: Settings) -> None:
    with make_session(settings.db_url) as session:
        widget = Widget(name="a")
        session.add(widget)
        session.commit()

        assert widget.created_at is not None
        assert widget.updated_at is not None


def test_updated_at_moves_forward_on_change(settings: Settings) -> None:
    with make_session(settings.db_url) as session:
        widget = Widget(name="a")
        session.add(widget)
        session.commit()
        first = widget.updated_at

        time.sleep(0.01)
        widget.name = "b"
        session.commit()

        assert widget.updated_at > first


@pytest.fixture(params=["memory", "file"])
def sqlite_url(request: pytest.FixtureRequest, tmp_path: Path) -> str:
    return "sqlite://" if request.param == "memory" else f"sqlite:///{tmp_path / 'fk.db'}"


def test_sqlite_enforces_foreign_keys(sqlite_url: str) -> None:
    with make_session(sqlite_url) as session:
        session.add(Child(id=1, parent_id=999))

        with pytest.raises(IntegrityError):
            session.commit()
