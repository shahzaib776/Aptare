"""Hand-written resumes shared by the template, renderer and golden tests.

Ids are fixed so golden snapshots never depend on randomness.
"""

from typing import Any
from uuid import UUID

from app.schemas.resume import TailoredResume


def uid(n: int) -> str:
    return str(UUID(int=n))


def bullet(n: int, text: str) -> dict[str, Any]:
    return {
        "id": uid(n),
        "source_bullet_id": uid(n + 1000),
        "text": text,
        "stretched_terms": [],
        "covered_keywords": [],
    }


def full_resume_data() -> dict[str, Any]:
    return {
        "header": {
            "full_name": "Ada Lovelace",
            "headline": "Engineer",
            "email": "ada@example.com",
            "phone": "555-0100",
            "location": "London",
            "links": [
                {
                    "kind": "linkedin",
                    "label": "linkedin.com/in/ada",
                    "url": "https://linkedin.com/in/ada",
                },
                {"kind": "github", "label": "github.com/ada", "url": "https://github.com/ada"},
            ],
        },
        "summary": "Builds reliable systems.",
        "sections": [
            {
                "key": "education",
                "items": [
                    {
                        "education_id": uid(1),
                        "institution": "MIT",
                        "degree": "BS",
                        "field": "Math",
                        "location": "Cambridge",
                        "dates": "2015 - 2019",
                        "details": ["Dean's list"],
                    }
                ],
            },
            {
                "key": "experience",
                "items": [
                    {
                        "experience_id": uid(2),
                        "variant_id": uid(3),
                        "title": "Engineer",
                        "company": "Analytical Engines",
                        "location": "London",
                        "dates": "2020 - Present",
                        "bullets": [bullet(10, "Cut costs by $5k")],
                    }
                ],
            },
            {
                "key": "projects",
                "items": [
                    {
                        "project_id": uid(4),
                        "name": "Difference Engine",
                        "url": "https://example.com/de",
                        "date": "2021",
                        "bullets": [bullet(11, "Built it")],
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
                            },
                            {"name": "Tools", "skills": [{"name": "Git", "stretched": False}]},
                        ]
                    }
                ],
            },
        ],
    }


def full_resume() -> TailoredResume:
    return TailoredResume.model_validate(full_resume_data())


def no_linkedin_resume() -> TailoredResume:
    data = full_resume_data()
    data["header"]["links"] = [x for x in data["header"]["links"] if x["kind"] != "linkedin"]
    return TailoredResume.model_validate(data)


def minimal_resume() -> TailoredResume:
    return TailoredResume.model_validate(
        {"header": {"full_name": "Ada", "email": "ada@example.com"}, "sections": []}
    )


def sparse_resume() -> TailoredResume:
    """Items with nothing optional filled in, plus a section with no items at all."""
    return TailoredResume.model_validate(
        {
            "header": {"full_name": "Ada"},
            "sections": [
                {"key": "education", "items": []},
                {
                    "key": "experience",
                    "items": [
                        {
                            "experience_id": uid(2),
                            "variant_id": uid(3),
                            "title": "Engineer",
                            "company": "Acme",
                            "dates": "2020",
                            "bullets": [],
                        }
                    ],
                },
                {
                    "key": "projects",
                    "items": [{"project_id": uid(4), "name": "Solo", "bullets": []}],
                },
            ],
        }
    )
