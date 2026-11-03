from uuid import uuid4

import pytest

from app.schemas.resume import (
    EducationSection,
    ExperienceSection,
    SkillsSection,
    TailoredResume,
)
from app.services.render.escape import escape_resume, escape_text


@pytest.mark.parametrize(
    ("raw", "escaped"),
    [
        ("\\", r"\textbackslash{}"),
        ("{", r"\{"),
        ("}", r"\}"),
        ("$", r"\$"),
        ("&", r"\&"),
        ("#", r"\#"),
        ("^", r"\textasciicircum{}"),
        ("_", r"\_"),
        ("~", r"\textasciitilde{}"),
        ("%", r"\%"),
    ],
)
def test_each_special_character_is_escaped(raw: str, escaped: str) -> None:
    assert escape_text(raw) == escaped


def test_characters_in_a_sentence_are_all_escaped() -> None:
    assert escape_text("50% & $30k") == r"50\% \& \$30k"


def test_escapes_are_not_escaped_again() -> None:
    # TP-6: one pass; a chain of replace() calls would re-escape the braces it just wrote.
    assert escape_text("a^b") == r"a\textasciicircum{}b"
    assert escape_text("50\\%") == r"50\textbackslash{}\%"


def test_text_that_looks_like_a_latex_command_stays_visible_text() -> None:
    assert escape_text(r"\input{/etc/passwd}") == r"\textbackslash{}input\{/etc/passwd\}"


@pytest.mark.parametrize(
    ("raw", "safe"),
    [
        ("\u2013", "--"),
        ("\u2014", "---"),
        ("\u2018x\u2019", "`x'"),
        ("\u201cx\u201d", "``x''"),
        ("a\u00a0b", "a~b"),
    ],
)
def test_unicode_dashes_quotes_and_nbsp_become_latex_safe(raw: str, safe: str) -> None:
    assert escape_text(raw) == safe


@pytest.mark.parametrize("plain", ["", "Plain text 2024", "café"])
def test_text_without_special_characters_is_unchanged(plain: str) -> None:
    assert escape_text(plain) == plain


def resume_with_specials() -> TailoredResume:
    return TailoredResume.model_validate(
        {
            "header": {
                "full_name": "Ada & Co",
                "links": [{"kind": "github", "label": "ada_l", "url": "https://x.com/a_b"}],
            },
            "summary": "Saved 50% of costs",
            "sections": [
                {
                    "key": "experience",
                    "items": [
                        {
                            "experience_id": str(uuid4()),
                            "variant_id": str(uuid4()),
                            "title": "Engineer",
                            "company": "R&D",
                            "dates": "2020 \u2013 2024",
                            "bullets": [
                                {
                                    "id": str(uuid4()),
                                    "source_bullet_id": str(uuid4()),
                                    "text": "Cut costs by $5k",
                                    "stretched_terms": [],
                                    "covered_keywords": [],
                                }
                            ],
                        }
                    ],
                },
                {
                    "key": "education",
                    "items": [
                        {
                            "education_id": str(uuid4()),
                            "institution": "MIT",
                            "degree": "BS",
                            "details": ["GPA #1"],
                        }
                    ],
                },
                {
                    "key": "skills",
                    "items": [
                        {
                            "categories": [
                                {"name": "C#", "skills": [{"name": "C++", "stretched": False}]}
                            ]
                        }
                    ],
                },
            ],
        }
    )


def test_escape_resume_escapes_text_in_every_part_of_the_resume() -> None:
    out = escape_resume(resume_with_specials())

    assert out.header.full_name == r"Ada \& Co"
    assert out.header.links[0].label == r"ada\_l"
    assert out.summary == r"Saved 50\% of costs"
    experience, education, skills = out.sections
    assert isinstance(experience, ExperienceSection)
    assert isinstance(education, EducationSection)
    assert isinstance(skills, SkillsSection)
    assert experience.items[0].company == r"R\&D"
    assert experience.items[0].dates == "2020 -- 2024"
    assert experience.items[0].bullets[0].text == r"Cut costs by \$5k"
    assert education.items[0].details == [r"GPA \#1"]
    assert skills.items[0].categories[0].name == r"C\#"


def test_escape_resume_keeps_ids_and_section_keys() -> None:
    resume = resume_with_specials()

    out = escape_resume(resume)

    assert [s.key for s in out.sections] == ["experience", "education", "skills"]
    before, after = resume.sections[0], out.sections[0]
    assert isinstance(before, ExperienceSection)
    assert isinstance(after, ExperienceSection)
    assert after.items[0].experience_id == before.items[0].experience_id


def test_escape_resume_does_not_change_the_resume_it_was_given() -> None:
    resume = resume_with_specials()

    escape_resume(resume)

    assert resume.header.full_name == "Ada & Co"
