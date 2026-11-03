import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from app.schemas.template import TemplateManifest
from app.services.render.templates import ManifestError, load_manifests

Manifest = dict[str, Any]


def valid_manifest() -> Manifest:
    return {
        "id": "dense-single",
        "name": "Dense single column",
        "license": "MIT",
        "fields": ["email", "phone", "github", "website"],
        "sections": [
            {"key": "experience", "column": "main", "movable": True, "required": True},
            {"key": "skills", "column": "side", "movable": False, "required": False},
        ],
        "typography_defaults": {
            "base_font_pt": 10.0,
            "line_spread": 1.0,
            "margin_in": 0.6,
            "item_sep_pt": 2.0,
            "section_sep_pt": 6.0,
        },
        "typography_bounds": {
            "base_font_pt": [9.0, 11.0],
            "line_spread": [0.9, 1.1],
            "margin_in": [0.4, 0.8],
            "item_sep_pt": [0.0, 4.0],
            "section_sep_pt": [2.0, 8.0],
        },
    }


def write_manifest(root: Path, folder: str, data: Manifest) -> None:
    (root / folder).mkdir()
    (root / folder / "manifest.json").write_text(json.dumps(data))


def test_a_valid_manifest_loads_and_reads_back_as_written(tmp_path: Path) -> None:
    write_manifest(tmp_path, "dense-single", valid_manifest())

    manifest = load_manifests(tmp_path)["dense-single"]

    assert manifest.fields == {"email", "phone", "github", "website"}
    assert [(s.key, s.column, s.movable) for s in manifest.sections] == [
        ("experience", "main", True),
        ("skills", "side", False),
    ]
    assert manifest.typography_defaults.margin_in == 0.6
    assert manifest.typography_bounds["margin_in"] == (0.4, 0.8)


def test_every_template_folder_is_loaded_and_everything_else_is_ignored(tmp_path: Path) -> None:
    write_manifest(tmp_path, "dense-single", valid_manifest())
    write_manifest(tmp_path, "classic-serif", {**valid_manifest(), "id": "classic-serif"})
    (tmp_path / "LICENSES.md").write_text("notes")
    (tmp_path / ".git").mkdir()
    (tmp_path / "_drafts").mkdir()

    assert sorted(load_manifests(tmp_path)) == ["classic-serif", "dense-single"]


def test_an_empty_templates_folder_has_no_templates(tmp_path: Path) -> None:
    assert load_manifests(tmp_path) == {}


def _set(path: tuple[str, ...], value: Any) -> Callable[[Manifest], None]:
    def mutate(manifest: Manifest) -> None:
        target = manifest
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value

    return mutate


def _drop_bound(manifest: Manifest) -> None:
    del manifest["typography_bounds"]["margin_in"]


def _duplicate_section(manifest: Manifest) -> None:
    manifest["sections"].append(manifest["sections"][0])


INVALID: dict[str, Callable[[Manifest], None]] = {
    "default_outside_its_bound": _set(("typography_defaults", "base_font_pt"), 12.0),
    "bound_with_min_above_max": _set(("typography_bounds", "base_font_pt"), [11.0, 9.0]),
    "missing_bound": _drop_bound,
    "unknown_bound_name": _set(("typography_bounds", "margin"), [0.1, 0.2]),
    "unknown_field": _set(("fields",), ["email", "fax"]),
    "duplicate_section": _duplicate_section,
    "unknown_section": _set(
        ("sections",), [{"key": "hobbies", "column": "main", "movable": True, "required": False}]
    ),
    "id_differs_from_folder": _set(("id",), "other-name"),
    "id_with_a_path": _set(("id",), "../escape"),
    "unknown_key": _set(("colour",), "red"),
    "empty_license": _set(("license",), ""),
}


@pytest.mark.parametrize("mutate", INVALID.values(), ids=INVALID.keys())
def test_an_invalid_manifest_is_rejected_and_names_its_folder(
    tmp_path: Path, mutate: Callable[[Manifest], None]
) -> None:
    data = valid_manifest()
    mutate(data)
    write_manifest(tmp_path, "dense-single", data)

    with pytest.raises(ManifestError, match="dense-single"):
        load_manifests(tmp_path)


def test_broken_json_is_rejected_and_names_its_folder(tmp_path: Path) -> None:
    (tmp_path / "dense-single").mkdir()
    (tmp_path / "dense-single" / "manifest.json").write_text("{not json")

    with pytest.raises(ManifestError, match="dense-single"):
        load_manifests(tmp_path)


def test_a_template_folder_without_a_manifest_is_an_error_not_a_silent_skip(
    tmp_path: Path,
) -> None:
    (tmp_path / "dense-single").mkdir()

    with pytest.raises(ManifestError, match=r"dense-single.*missing"):
        load_manifests(tmp_path)


def test_the_id_cannot_hold_a_path() -> None:
    # The loader also rejects this id (it differs from the folder), so test the schema alone.
    with pytest.raises(ValidationError):
        TemplateManifest.model_validate({**valid_manifest(), "id": "../escape"})


def test_a_manifest_that_is_not_utf8_names_its_folder(tmp_path: Path) -> None:
    # PowerShell's `>` writes UTF-16, which is an easy way to produce one by accident.
    (tmp_path / "dense-single").mkdir()
    (tmp_path / "dense-single" / "manifest.json").write_bytes(
        json.dumps(valid_manifest()).encode("utf-16")
    )

    with pytest.raises(ManifestError, match="dense-single"):
        load_manifests(tmp_path)


def test_a_manifest_that_cannot_be_read_names_its_folder(tmp_path: Path) -> None:
    (tmp_path / "dense-single" / "manifest.json").mkdir(parents=True)

    with pytest.raises(ManifestError, match="dense-single"):
        load_manifests(tmp_path)
