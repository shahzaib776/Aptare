import re
from pathlib import Path
from uuid import uuid4

import pytest
from jinja2 import UndefinedError

from app.schemas.resume import TailoredResume
from app.schemas.typography import Typography
from app.services.render.escape import escape_resume
from app.services.render.jinja_env import make_environment
from app.services.render.templates import load_manifests
from tests.resumes import full_resume, minimal_resume, sparse_resume

TEMPLATES = Path(__file__).resolve().parents[3] / "templates"
TEMPLATE_IDS = sorted(
    p.name for p in TEMPLATES.iterdir() if p.is_dir() and not p.name.startswith((".", "_"))
)


def render(template_id: str, resume: TailoredResume, typography: Typography | None = None) -> str:
    manifest = load_manifests(TEMPLATES)[template_id]
    template = make_environment(TEMPLATES).get_template(f"{template_id}/template.tex.j2")
    return template.render(
        resume=escape_resume(resume), typography=typography or manifest.typography_defaults
    )


def contact_block(tex: str) -> str:
    return tex.split(r"\begin{center}")[1].split(r"\end{center}")[0]


def test_there_is_at_least_one_template_to_check() -> None:
    assert "dense-single" in TEMPLATE_IDS


@pytest.mark.parametrize("template_id", TEMPLATE_IDS)
def test_every_template_folder_has_a_valid_manifest_with_a_matching_id(template_id: str) -> None:
    assert template_id in load_manifests(TEMPLATES)


@pytest.mark.parametrize("template_id", TEMPLATE_IDS)
def test_a_full_resume_renders_with_no_template_syntax_left(template_id: str) -> None:
    tex = render(template_id, full_resume())

    assert r"\VAR{" not in tex
    assert r"\BLOCK{" not in tex
    assert not re.search(r"^\s*%%", tex, re.MULTILINE)
    for text in ("Ada Lovelace", "Cut costs by \\$5k", "Analytical Engines", "Python", "Git"):
        assert text in tex


@pytest.mark.parametrize("template_id", TEMPLATE_IDS)
def test_machine_readable_text_is_switched_on_only_where_the_engine_has_it(
    template_id: str,
) -> None:
    tex = render(template_id, full_resume())

    guarded = re.search(r"\\ifdefined\\pdfgentounicode(.*?)\\fi", tex, re.DOTALL)
    assert guarded is not None
    assert r"\pdfgentounicode=1" in guarded.group(1)
    assert r"\input{glyphtounicode}" in guarded.group(1)
    assert tex.count(r"\pdfgentounicode") == 2
    assert tex.count(r"\input{glyphtounicode}") == 1


@pytest.mark.parametrize("template_id", TEMPLATE_IDS)
def test_a_name_and_email_alone_leave_no_separator_or_empty_link(template_id: str) -> None:
    tex = render(template_id, minimal_resume())

    assert "$|$" not in contact_block(tex)
    assert r"\href{}" not in tex
    assert "ada@example.com" in contact_block(tex)


@pytest.mark.parametrize("template_id", TEMPLATE_IDS)
def test_contact_items_are_joined_by_exactly_one_separator_each(template_id: str) -> None:
    tex = render(template_id, full_resume())

    # phone, email, location and two links make five items and so four separators
    assert contact_block(tex).count("$|$") == 4


@pytest.mark.parametrize("template_id", TEMPLATE_IDS)
def test_things_with_nothing_in_them_produce_no_empty_lists_headings_or_separators(
    template_id: str,
) -> None:
    tex = render(template_id, sparse_resume())

    assert not re.search(r"\\resumeItemListStart\s*\\resumeItemListEnd", tex)
    assert not re.search(r"\\resumeSubHeadingListStart\s*\\resumeSubHeadingListEnd", tex)
    assert r"\section{Education}" not in tex
    assert r"\section{Experience}" in tex
    assert "Solo} $|$" not in tex


@pytest.mark.parametrize("template_id", TEMPLATE_IDS)
def test_typography_values_reach_the_output(template_id: str) -> None:
    typography = Typography(
        base_font_pt=9.5, line_spread=1.05, margin_in=0.7, item_sep_pt=3.0, section_sep_pt=7.0
    )

    tex = render(template_id, full_resume(), typography)

    assert "margin=0.7in" in tex
    assert r"\linespread{1.05}" in tex
    assert "itemsep=3.0pt" in tex
    assert r"{7.0pt}" in tex
    assert r"\fontsize{9.5}{11.4}" in tex


@pytest.mark.parametrize("template_id", TEMPLATE_IDS)
def test_a_missing_variable_fails_loudly(template_id: str) -> None:
    template = make_environment(TEMPLATES).get_template(f"{template_id}/template.tex.j2")

    with pytest.raises(UndefinedError):
        template.render(resume=escape_resume(full_resume()))


def skills_resume(*groups: tuple[str, list[str]]) -> TailoredResume:
    categories = [
        {"name": name, "skills": [{"name": s, "stretched": False} for s in skills]}
        for name, skills in groups
    ]
    return TailoredResume.model_validate(
        {
            "header": {"full_name": "Ada"},
            "sections": [{"key": "skills", "items": [{"categories": categories}]}],
        }
    )


@pytest.mark.parametrize("template_id", TEMPLATE_IDS)
def test_a_skill_group_with_no_skills_leaves_no_dangling_label(template_id: str) -> None:
    tex = render(template_id, skills_resume(("Languages", ["Python"]), ("Empty", [])))

    assert "Languages" in tex
    assert "Empty" not in tex
    assert r"\\" not in tex.split(r"\section{Technical Skills}")[1].split(r"\end{itemize}")[0]


@pytest.mark.parametrize("template_id", TEMPLATE_IDS)
def test_a_skills_section_whose_groups_are_all_empty_is_left_out(template_id: str) -> None:
    tex = render(template_id, skills_resume(("Empty", [])))

    assert "Technical Skills" not in tex


@pytest.mark.parametrize("template_id", TEMPLATE_IDS)
def test_an_education_entry_with_only_the_required_fields_has_no_stray_parts(
    template_id: str,
) -> None:
    resume = TailoredResume.model_validate(
        {
            "header": {"full_name": "Ada"},
            "sections": [
                {
                    "key": "education",
                    "items": [
                        {
                            "education_id": str(uuid4()),
                            "institution": "MIT",
                            "degree": "BS",
                            "details": [],
                        }
                    ],
                }
            ],
        }
    )

    tex = render(template_id, resume)

    assert "{BS}" in tex
    assert "BS," not in tex
    assert r"\resumeItemListStart" not in tex.split(r"\begin{document}")[1]


@pytest.mark.parametrize("template_id", TEMPLATE_IDS)
def test_a_project_with_a_url_links_to_it_after_a_separator(template_id: str) -> None:
    tex = render(template_id, full_resume())

    assert r"\ $|$\ \href{https://example.com/de}" in tex


@pytest.mark.parametrize("template_id", TEMPLATE_IDS)
def test_separators_never_rely_on_a_space_at_the_start_of_a_line(template_id: str) -> None:
    """Found by compiling (step 8): TeX drops spaces at the start of a line."""
    tex = render(template_id, full_resume())

    assert not re.search(r"^ *\$\|\$", tex, re.MULTILINE)
