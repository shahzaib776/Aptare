from pathlib import Path

from pydantic import ValidationError

from app.errors import AppError
from app.schemas.template import TemplateManifest


class ManifestError(Exception):
    pass


def load_manifests(templates_dir: Path) -> dict[str, TemplateManifest]:
    """Load every template's manifest by id; a broken one fails loudly rather than vanishing."""
    manifests: dict[str, TemplateManifest] = {}
    for folder in sorted(templates_dir.iterdir()):
        if folder.is_dir() and not folder.name.startswith((".", "_")):
            manifest = _load_one(folder)
            manifests[manifest.id] = manifest
    return manifests


def find_template(manifests: dict[str, TemplateManifest], template_id: str) -> TemplateManifest:
    if template_id not in manifests:
        raise AppError("template_not_found", "No such template.", 404)
    return manifests[template_id]


def _load_one(folder: Path) -> TemplateManifest:
    try:
        text = (folder / "manifest.json").read_text(encoding="utf-8")
        manifest = TemplateManifest.model_validate_json(text)
    except FileNotFoundError as exc:
        raise ManifestError(f"{folder.name}: manifest.json is missing") from exc
    except (OSError, UnicodeDecodeError) as exc:
        raise ManifestError(f"{folder.name}: cannot read manifest.json ({exc})") from exc
    except ValidationError as exc:
        problems = "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in exc.errors())
        raise ManifestError(f"{folder.name}: invalid manifest ({problems})") from exc

    if manifest.id != folder.name:
        raise ManifestError(f"{folder.name}: id {manifest.id!r} must equal the folder name")
    return manifest
