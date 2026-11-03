import time
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.config import Settings
from app.db import UuidV7, make_engine, make_session_factory, new_uuid7
from app.models.base import Base, TimestampMixin


class Widget(TimestampMixin, Base):
    __tablename__ = "widgets_test"

    id: Mapped[uuid.UUID] = mapped_column(UuidV7, primary_key=True, default=new_uuid7)
    name: Mapped[str]


def make_session(settings: Settings) -> Session:
    engine = make_engine(settings.db_url)
    Base.metadata.create_all(engine)
    return make_session_factory(engine)()


def test_uuid_column_round_trips_a_real_uuid(settings: Settings) -> None:
    with make_session(settings) as session:
        widget = Widget(name="a")
        session.add(widget)
        session.commit()
        stored_id = widget.id

        loaded = session.scalars(select(Widget)).one()

    assert isinstance(loaded.id, uuid.UUID)
    assert loaded.id == stored_id
    assert loaded.id.version == 7


def test_timestamps_are_set_on_insert(settings: Settings) -> None:
    with make_session(settings) as session:
        widget = Widget(name="a")
        session.add(widget)
        session.commit()

        assert widget.created_at is not None
        assert widget.updated_at is not None


def test_updated_at_moves_forward_on_change(settings: Settings) -> None:
    with make_session(settings) as session:
        widget = Widget(name="a")
        session.add(widget)
        session.commit()
        first = widget.updated_at

        time.sleep(0.01)
        widget.name = "b"
        session.commit()

        assert widget.updated_at > first
