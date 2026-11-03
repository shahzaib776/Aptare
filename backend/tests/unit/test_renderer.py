from pathlib import Path

import pytest

from app.schemas.resume import ExperienceSection, SectionKey, TailoredResume
from app.schemas.template import FieldKey, SectionSpec, TemplateManifest
from app.schemas.typography import Typography
from app.services.render.renderer import TexBundle, order_sections, render
from app.services.render.templates import load_manifests
from tests.resumes import full_resume, minimal_resume

TEMPLATES = Path(__file__).resolve().parents[3] / "templates"


def dense_single() -> TemplateManifest:
    return load_manifests(TEMPLATES)["dense-single"]


def bundle(
    resume: TailoredResume,
    manifest: TemplateManifest | None = None,
    typography: Typography | None = None,
    section_order: list[SectionKey] | None = None,
    hidden_fields: set[FieldKey] | None = None,
    templates_dir: Path = TEMPLATES,
) -> TexBundle:
    manifest = manifest or dense_single()
    return render(
        resume,
        manifest,
        typography or manifest.typography_defaults,
        section_order or [],
        hidden_fields or set(),
        templates_dir=templates_dir,
    )


def tex_of(
    resume: TailoredResume,
    manifest: TemplateManifest | None = None,
    section_order: list[SectionKey] | None = None,
    hidden_fields: set[FieldKey] | None = None,
) -> str:
    return bundle(resume, manifest, section_order=section_order, hidden_fields=hidden_fields).tex


def contact_block(tex: str) -> str:
    return tex.split(r"\begin{center}")[1].split(r"\end{center}")[0]


def specs(*items: tuple[str, str, bool]) -> list[SectionSpec]:
    return [
        SectionSpec.model_validate({"key": k, "column": c, "movable": m, "required": False})
        for k, c, m in items
    ]


# --- fields -----------------------------------------------------------------------------------


def test_a_field_the_manifest_does_not_declare_is_left_out() -> None:
    manifest = dense_single()
    without_linkedin = manifest.model_copy(update={"fields": manifest.fields - {"linkedin"}})

    assert "linkedin.com/in/ada" in tex_of(full_resume(), manifest)
    tex = tex_of(full_resume(), without_linkedin)
    assert "linkedin.com/in/ada" not in tex
    assert "github.com/ada" in tex


def test_a_hidden_field_is_left_out_without_leaving_a_separator_behind() -> None:
    tex = tex_of(full_resume(), hidden_fields={"email"})

    assert "mailto:" not in tex
    # phone, location, linkedin and github remain: four items, three separators
    assert contact_block(tex).count("$|$") == 3


HEADER_FIELDS = [
    ("headline", "Engineer"),
    ("email", "ada@example.com"),
    ("phone", "555-0100"),
    ("location", "London"),
]


@pytest.mark.parametrize(("field", "text"), HEADER_FIELDS)
def test_every_header_field_can_be_hidden(field: FieldKey, text: str) -> None:
    assert text in contact_block(tex_of(full_resume()))

    assert text not in contact_block(tex_of(full_resume(), hidden_fields={field}))


@pytest.mark.parametrize(("field", "text"), HEADER_FIELDS)
def test_every_header_field_is_left_out_when_the_manifest_does_not_declare_it(
    field: FieldKey, text: str
) -> None:
    manifest = dense_single()
    without = manifest.model_copy(update={"fields": manifest.fields - {field}})

    assert text not in contact_block(tex_of(full_resume(), without))


def test_hiding_the_summary_drops_the_summary_section() -> None:
    assert r"\section{Summary}" in tex_of(full_resume())
    assert r"\section{Summary}" not in tex_of(full_resume(), hidden_fields={"summary"})


def test_hiding_a_link_kind_drops_only_those_links() -> None:
    tex = tex_of(full_resume(), hidden_fields={"github"})

    assert "github.com/ada" not in tex
    assert "linkedin.com/in/ada" in tex


def test_an_empty_optional_field_leaves_no_label_or_separator() -> None:
    tex = tex_of(minimal_resume())

    assert "$|$" not in contact_block(tex)
    assert r"\href{}" not in tex


def test_rendering_does_not_change_the_resume_it_was_given() -> None:
    resume = full_resume()
    before = resume.model_copy(deep=True)

    tex_of(resume, hidden_fields={"email", "github", "summary"})

    assert resume == before


def test_text_is_escaped_exactly_once() -> None:
    resume = TailoredResume.model_validate({"header": {"full_name": "R&D 50% $5k"}, "sections": []})

    tex = tex_of(resume)

    assert r"R\&D 50\% \$5k" in tex
    assert r"\textbackslash" not in tex


# --- sections ---------------------------------------------------------------------------------


def test_sections_follow_section_order() -> None:
    tex = tex_of(full_resume(), section_order=["skills", "projects", "experience", "education"])

    headings = [r"\section{Technical Skills}", r"\section{Projects}", r"\section{Experience}"]
    positions = [tex.index(h) for h in headings]
    assert positions == sorted(positions)
    assert tex.index(r"\section{Experience}") < tex.index(r"\section{Education}")


def test_a_section_the_manifest_does_not_declare_is_dropped() -> None:
    manifest = dense_single().model_copy(update={"sections": specs(("experience", "main", True))})

    tex = tex_of(full_resume(), manifest)

    assert r"\section{Experience}" in tex
    assert r"\section{Education}" not in tex
    assert r"\section{Projects}" not in tex


def test_order_sections_follows_the_requested_order() -> None:
    manifest = specs(
        ("education", "main", True),
        ("experience", "main", True),
        ("projects", "main", True),
        ("skills", "main", True),
    )

    assert order_sections(manifest, ["skills", "projects", "experience", "education"]) == [
        "skills",
        "projects",
        "experience",
        "education",
    ]


def test_a_fixed_section_keeps_its_place() -> None:
    manifest = specs(
        ("education", "main", True),
        ("experience", "main", False),
        ("projects", "main", True),
        ("skills", "main", True),
    )

    assert order_sections(manifest, ["skills", "projects", "education"]) == [
        "skills",
        "experience",
        "projects",
        "education",
    ]


def test_sections_missing_from_the_requested_order_follow_in_manifest_order() -> None:
    manifest = specs(
        ("education", "main", True),
        ("experience", "main", True),
        ("projects", "main", True),
        ("skills", "main", True),
    )

    assert order_sections(manifest, ["projects"]) == [
        "projects",
        "education",
        "experience",
        "skills",
    ]


def test_keys_the_manifest_does_not_have_are_ignored() -> None:
    manifest = specs(("education", "main", True), ("experience", "main", True))

    assert order_sections(manifest, ["skills", "experience", "education"]) == [
        "experience",
        "education",
    ]


def test_a_section_never_leaves_its_column() -> None:
    manifest = specs(
        ("experience", "main", True),
        ("projects", "main", True),
        ("skills", "side", True),
        ("education", "side", True),
    )

    interleaved: list[SectionKey] = ["skills", "education", "projects", "experience"]
    assert order_sections(manifest, interleaved) == [
        "projects",
        "experience",
        "skills",
        "education",
    ]
    swapped: list[SectionKey] = ["education", "skills", "experience", "projects"]
    assert order_sections(manifest, swapped) == ["experience", "projects", "education", "skills"]


# --- the hash ---------------------------------------------------------------------------------


def mini_templates(tmp_path: Path, assets: dict[str, str]) -> tuple[Path, TemplateManifest]:
    folder = tmp_path / "mini"
    folder.mkdir()
    (folder / "template.tex.j2").write_text(r"\VAR{resume.header.full_name}")
    for name, content in assets.items():
        (folder / "assets").mkdir(exist_ok=True)
        (folder / "assets" / name).write_text(content)
    return tmp_path, dense_single().model_copy(update={"id": "mini"})


def test_the_same_input_gives_the_same_hash() -> None:
    assert bundle(full_resume()).tex_hash == bundle(full_resume()).tex_hash


def test_changed_text_changes_the_hash() -> None:
    assert bundle(full_resume()).tex_hash != bundle(minimal_resume()).tex_hash


def test_changed_typography_changes_the_hash() -> None:
    wider = dense_single().typography_defaults.model_copy(update={"margin_in": 0.9})

    assert bundle(full_resume()).tex_hash != bundle(full_resume(), typography=wider).tex_hash


def test_a_template_without_an_assets_folder_has_no_assets() -> None:
    assert bundle(full_resume()).assets == []


def test_assets_are_listed_in_sorted_order_and_part_of_the_hash(tmp_path: Path) -> None:
    root, manifest = mini_templates(tmp_path, {"b.cls": "second", "a.cls": "first"})

    result = bundle(minimal_resume(), manifest, templates_dir=root)
    assert [p.name for p in result.assets] == ["a.cls", "b.cls"]

    (root / "mini" / "assets" / "a.cls").write_text("changed")
    changed = bundle(minimal_resume(), manifest, templates_dir=root)
    assert changed.tex_hash != result.tex_hash


def test_the_bundle_carries_the_resume_as_rendered() -> None:
    """Step 9: the compile cache builds its element list from this, so it must match the .tex."""
    resume = full_resume()

    result = bundle(resume, section_order=["projects", "experience"], hidden_fields={"summary"})

    assert result.visible.summary is None
    assert [s.key for s in result.visible.sections][:2] == ["projects", "experience"]
    experience = result.visible.sections[1]
    assert isinstance(experience, ExperienceSection)
    assert experience.items[0].bullets[0].text == "Cut costs by $5k"
    assert r"Cut costs by \$5k" in result.tex
