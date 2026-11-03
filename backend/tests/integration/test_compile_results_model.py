import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import make_engine, make_session_factory
from app.models.base import Base
from app.models.compile_result import CompileResult


@pytest.fixture
def session() -> Session:
    engine = make_engine("sqlite://")
    Base.metadata.create_all(engine)
    return make_session_factory(engine)()


def row(tex_hash: str = "t" * 64, elements_hash: str = "e" * 64) -> CompileResult:
    return CompileResult(
        tex_hash=tex_hash,
        elements_hash=elements_hash,
        pdf_hash="p" * 64,
        page_count=1,
        last_page_fill=0.5,
        text_map={"b1": [{"page": 0, "rect": [1.0, 2.0, 3.0, 4.0]}]},
    )


def test_a_row_round_trips_with_its_text_map(session: Session) -> None:
    session.add(row())
    session.commit()

    stored = session.scalars(select(CompileResult)).one()

    assert stored.text_map == {"b1": [{"page": 0, "rect": [1.0, 2.0, 3.0, 4.0]}]}
    assert stored.id is not None and stored.created_at is not None


def test_the_same_text_with_different_elements_is_a_separate_row(session: Session) -> None:
    session.add_all([row(elements_hash="1" * 64), row(elements_hash="2" * 64)])

    session.commit()


def test_the_same_text_and_elements_cannot_be_stored_twice(session: Session) -> None:
    session.add_all([row(), row()])

    with pytest.raises(IntegrityError):
        session.commit()
