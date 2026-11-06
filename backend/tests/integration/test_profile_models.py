import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import make_engine, make_session_factory, new_uuid7
from app.models.app_settings import AppSettings
from app.models.base import Base
from app.models.profile import (
    Bullet,
    BulletVariant,
    Education,
    Experience,
    Profile,
    Project,
    SkillCategory,
    Variant,
)


@pytest.fixture
def session() -> Session:
    engine = make_engine("sqlite://")
    Base.metadata.create_all(engine)
    return make_session_factory(engine)()


def count(session: Session, model: type[Base]) -> int:
    return session.scalar(select(func.count()).select_from(model)) or 0


def role(session: Session) -> tuple[Profile, Experience, Variant, Bullet]:
    """A profile with one experience, one title and one bullet linked to it."""
    profile = Profile(full_name="Ada Lovelace")
    session.add(profile)
    session.flush()
    experience = Experience(profile_id=profile.id, company="Acme", start_date="2022-06")
    session.add(experience)
    session.flush()
    variant = Variant(experience_id=experience.id, title="Engineer")
    bullet = Bullet(experience_id=experience.id, text="Built a crawler")
    session.add_all([variant, bullet])
    session.flush()
    session.add(BulletVariant(bullet_id=bullet.id, variant_id=variant.id))
    session.commit()
    return profile, experience, variant, bullet


def test_a_profile_with_every_section_round_trips(session: Session) -> None:
    profile, experience, _, bullet = role(session)
    profile.links = [{"kind": "github", "label": "gh", "url": "https://github.com/ada"}]
    bullet.skills = ["Python", "asyncio"]
    bullet.pinned = True
    bullet.embedding = b"\x00\x01\x02"
    session.add_all(
        [
            Project(profile_id=profile.id, name="Engine", date="2021-03"),
            Education(
                profile_id=profile.id, institution="MIT", degree="BS", details=["Dean's list"]
            ),
            SkillCategory(profile_id=profile.id, name="Languages", skills=["Python", "Go"]),
        ]
    )
    session.commit()
    session.expire_all()

    stored = session.get(Profile, profile.id)
    assert stored is not None
    assert stored.links == [{"kind": "github", "label": "gh", "url": "https://github.com/ada"}]
    assert session.get(Experience, experience.id).end_date is None  # type: ignore[union-attr]
    kept = session.get(Bullet, bullet.id)
    assert kept is not None
    assert (kept.skills, kept.pinned, kept.embedding) == (
        ["Python", "asyncio"],
        True,
        b"\x00\x01\x02",
    )
    assert session.scalars(select(Education)).one().details == ["Dean's list"]
    assert session.scalars(select(SkillCategory)).one().skills == ["Python", "Go"]


def test_deleting_a_profile_removes_everything_under_it(session: Session) -> None:
    profile, *_ = role(session)
    session.add_all(
        [
            Project(profile_id=profile.id, name="Engine"),
            Education(profile_id=profile.id, institution="MIT", degree="BS"),
            SkillCategory(profile_id=profile.id, name="Languages"),
        ]
    )
    session.commit()

    session.delete(profile)
    session.commit()

    for model in (Experience, Variant, Bullet, BulletVariant, Project, Education, SkillCategory):
        assert count(session, model) == 0, model.__name__


def test_deleting_a_variant_removes_its_links_but_keeps_the_bullet(session: Session) -> None:
    _, _, variant, _ = role(session)

    session.delete(variant)
    session.commit()

    assert count(session, BulletVariant) == 0
    assert count(session, Bullet) == 1


def test_deleting_a_bullet_removes_its_links(session: Session) -> None:
    *_, bullet = role(session)

    session.delete(bullet)
    session.commit()

    assert count(session, BulletVariant) == 0
    assert count(session, Variant) == 1


def test_a_project_owns_bullets_that_go_with_it(session: Session) -> None:
    profile, *_ = role(session)
    project = Project(profile_id=profile.id, name="Engine")
    session.add(project)
    session.flush()
    session.add(Bullet(project_id=project.id, text="Shipped v1"))
    session.commit()

    session.delete(project)
    session.commit()

    assert count(session, Bullet) == 1  # only the experience's bullet is left


def test_a_bullet_needs_exactly_one_owner(session: Session) -> None:
    profile, experience, *_ = role(session)
    project = Project(profile_id=profile.id, name="Engine")
    session.add(project)
    session.flush()

    session.add(Bullet(experience_id=experience.id, project_id=project.id, text="Both"))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()

    session.add(Bullet(text="Neither"))
    with pytest.raises(IntegrityError):
        session.commit()


def test_the_same_bullet_and_variant_cannot_be_linked_twice(session: Session) -> None:
    _, _, variant, bullet = role(session)

    session.add(BulletVariant(bullet_id=bullet.id, variant_id=variant.id))

    with pytest.raises(IntegrityError):
        session.commit()


def test_a_link_to_a_variant_that_does_not_exist_is_rejected(session: Session) -> None:
    *_, bullet = role(session)

    session.add(BulletVariant(bullet_id=bullet.id, variant_id=new_uuid7()))

    with pytest.raises(IntegrityError):
        session.commit()


def test_onboarding_starts_pending_with_no_defaults(session: Session) -> None:
    session.add(AppSettings())
    session.commit()

    settings = session.scalars(select(AppSettings)).one()

    assert (settings.profile_step, settings.provider_step) == ("pending", "pending")
    assert settings.resume_defaults == {}
