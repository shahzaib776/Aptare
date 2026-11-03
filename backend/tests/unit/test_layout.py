from pathlib import Path

import pytest

from app.errors import AppError
from app.schemas.resume import SectionKey
from app.schemas.template import TemplateManifest
from app.schemas.typography import Typography
from app.services.render.layout import check_layout
from app.services.render.templates import load_manifests

TEMPLATES = Path(__file__).resolve().parents[3] / "templates"


@pytest.fixture
def manifest() -> TemplateManifest:
    return load_manifests(TEMPLATES)["dense-single"]


def with_value(manifest: TemplateManifest, name: str, value: float) -> Typography:
    return manifest.typography_defaults.model_copy(update={name: value})


def test_the_template_defaults_and_an_empty_order_are_fine(manifest: TemplateManifest) -> None:
    check_layout(manifest, manifest.typography_defaults, [])


@pytest.mark.parametrize("edge", [0, 1])
def test_values_exactly_on_a_bound_are_allowed(manifest: TemplateManifest, edge: int) -> None:
    for name, bounds in manifest.typography_bounds.items():
        check_layout(manifest, with_value(manifest, name, bounds[edge]), [])


@pytest.mark.parametrize(("edge", "nudge"), [(0, -0.01), (1, 0.01)])
def test_values_just_outside_a_bound_are_rejected_with_the_field_named(
    manifest: TemplateManifest, edge: int, nudge: float
) -> None:
    for name, bounds in manifest.typography_bounds.items():
        value = bounds[edge] + nudge

        with pytest.raises(AppError) as raised:
            check_layout(manifest, with_value(manifest, name, value), [])

        error = raised.value
        assert (error.code, error.status_code) == ("typography_out_of_bounds", 422)
        assert error.details == {"field": name, "allowed": list(bounds), "given": value}


def test_a_valid_order_is_fine(manifest: TemplateManifest) -> None:
    check_layout(manifest, manifest.typography_defaults, ["skills", "experience"])


def test_a_repeated_section_is_rejected(manifest: TemplateManifest) -> None:
    order: list[SectionKey] = ["experience", "skills", "experience"]

    with pytest.raises(AppError) as raised:
        check_layout(manifest, manifest.typography_defaults, order)

    assert (raised.value.code, raised.value.status_code) == ("invalid_section_order", 422)


def test_a_section_the_template_does_not_have_is_rejected(manifest: TemplateManifest) -> None:
    without_projects = manifest.model_copy(
        update={"sections": [s for s in manifest.sections if s.key != "projects"]}
    )

    with pytest.raises(AppError) as raised:
        check_layout(without_projects, manifest.typography_defaults, ["projects"])

    assert raised.value.code == "invalid_section_order"
    assert raised.value.details == {"keys": ["projects"]}
