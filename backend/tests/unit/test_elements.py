from uuid import UUID

from app.schemas.resume import TailoredResume
from app.services.compile.elements import elements_from
from tests.resumes import bullet, full_resume_data, tricky_resume, uid


def resume_with(**changes: object) -> TailoredResume:
    return TailoredResume.model_validate({**full_resume_data(), **changes})


def test_summary_comes_first_then_bullets_in_render_order() -> None:
    data = full_resume_data()
    data["sections"][1]["items"][0]["bullets"] = [bullet(10, "First"), bullet(12, "Second")]

    elements = elements_from(TailoredResume.model_validate(data))

    assert [(e.id, e.text) for e in elements] == [
        ("summary", "Builds reliable systems."),
        (uid(10), "First"),
        (uid(12), "Second"),
        (uid(11), "Built it"),
    ]


def test_bullet_ids_are_uuid_strings() -> None:
    ids = [e.id for e in elements_from(resume_with()) if e.id != "summary"]

    assert all(str(UUID(i)) == i for i in ids)


def test_text_is_plain_not_escaped() -> None:
    texts = [e.text for e in elements_from(tricky_resume())]

    assert "Cut R&D costs 30% using C# & $5k_budget ~ 2^3 {braces}" in texts


def test_no_summary_means_no_summary_element() -> None:
    assert "summary" not in [e.id for e in elements_from(resume_with(summary=None))]


def test_sections_without_bullets_add_nothing() -> None:
    skills_only = [s for s in full_resume_data()["sections"] if s["key"] == "skills"]
    resume = resume_with(summary=None, sections=skills_only)

    assert elements_from(resume) == []
