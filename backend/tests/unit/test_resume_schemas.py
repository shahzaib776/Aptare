from typing import Any
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.resume import (
    ProjectsSection,
    TailoredBullet,
    TailoredResume,
)
from app.schemas.typography import Typography


def bullet_data() -> dict[str, Any]:
    return {
        "id": str(uuid4()),
        "source_bullet_id": str(uuid4()),
        "text": "Cut p95 latency by 40%",
        "stretched_terms": [],
        "covered_keywords": ["latency"],
    }


def full_resume_data() -> dict[str, Any]:
    return {
        "header": {
            "full_name": "Ada Lovelace",
            "headline": "Engineer",
            "email": "ada@example.com",
            "phone": "+1 555 0100",
            "location": "London",
            "links": [{"kind": "github", "label": "ada", "url": "https://github.com/ada"}],
        },
        "summary": "Builds reliable systems.",
        "sections": [
            {
                "key": "experience",
                "items": [
                    {
                        "experience_id": str(uuid4()),
                        "variant_id": str(uuid4()),
                        "title": "Engineer",
                        "company": "Analytical Engines",
                        "location": "London",
                        "dates": "Jan 2020 - Present",
                        "bullets": [bullet_data()],
                    }
                ],
            },
            {
                "key": "projects",
                "items": [
                    {
                        "project_id": str(uuid4()),
                        "name": "Difference Engine",
                        "url": None,
                        "date": "2021",
                        "bullets": [bullet_data()],
                    }
                ],
            },
            {
                "key": "education",
                "items": [
                    {
                        "education_id": str(uuid4()),
                        "institution": "Self-taught",
                        "degree": "Mathematics",
                        "field": None,
                        "location": None,
                        "dates": "1830 - 1835",
                        "details": ["Studied with De Morgan"],
                    }
                ],
            },
            {
                "key": "skills",
                "items": [
                    {
                        "categories": [
                            {
                                "name": "Languages",
                                "skills": [{"name": "Python", "stretched": False}],
                            }
                        ]
                    }
                ],
            },
        ],
    }


def test_a_full_resume_survives_a_json_round_trip() -> None:
    resume = TailoredResume.model_validate(full_resume_data())

    again = TailoredResume.model_validate_json(resume.model_dump_json())

    assert again == resume


def test_the_smallest_resume_is_just_a_name_and_no_sections() -> None:
    resume = TailoredResume.model_validate({"header": {"full_name": "Ada"}, "sections": []})

    assert resume.summary is None
    assert resume.header.email is None
    assert resume.header.links == []


def test_a_bullet_is_unlocked_unless_told_otherwise() -> None:
    assert TailoredBullet.model_validate(bullet_data()).locked is False


def test_an_unknown_key_is_rejected_instead_of_ignored() -> None:
    with pytest.raises(ValidationError):
        TailoredBullet.model_validate({**bullet_data(), "invented_metric": "99%"})


def test_the_section_key_decides_which_kind_of_section_it_is() -> None:
    resume = TailoredResume.model_validate(full_resume_data())

    assert isinstance(resume.sections[1], ProjectsSection)


def test_an_unknown_section_key_is_rejected() -> None:
    data = {"header": {"full_name": "Ada"}, "sections": [{"key": "hobbies", "items": []}]}

    with pytest.raises(ValidationError):
        TailoredResume.model_validate(data)


def test_a_section_cannot_hold_the_wrong_kind_of_item() -> None:
    wrong = {"key": "education", "items": [{"name": "Not an education item"}]}

    with pytest.raises(ValidationError):
        TailoredResume.model_validate({"header": {"full_name": "Ada"}, "sections": [wrong]})


def test_typography_needs_all_five_values() -> None:
    complete = {
        "base_font_pt": 10.0,
        "line_spread": 1.0,
        "margin_in": 0.5,
        "item_sep_pt": 2.0,
        "section_sep_pt": 6.0,
    }
    assert Typography.model_validate(complete).margin_in == 0.5

    del complete["margin_in"]
    with pytest.raises(ValidationError):
        Typography.model_validate(complete)


@pytest.mark.parametrize("bad", ["NaN", "Infinity", "-Infinity"])
def test_typography_rejects_values_that_are_not_real_numbers(bad: str) -> None:
    raw = (
        f'{{"base_font_pt": {bad}, "line_spread": 1.0, "margin_in": 0.5,'
        ' "item_sep_pt": 2.0, "section_sep_pt": 6.0}'
    )

    with pytest.raises(ValidationError):
        Typography.model_validate_json(raw)
