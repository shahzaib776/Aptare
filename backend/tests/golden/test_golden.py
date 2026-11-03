from collections.abc import Callable
from pathlib import Path

import pytest

from app.schemas.resume import TailoredResume
from app.services.render.renderer import render
from app.services.render.templates import load_manifests
from tests.resumes import full_resume, minimal_resume, no_linkedin_resume, tricky_resume

TEMPLATES = Path(__file__).resolve().parents[3] / "templates"
GOLDEN = Path(__file__).resolve().parent / "dense-single"

RESUMES: dict[str, Callable[[], TailoredResume]] = {
    "full": full_resume,
    "minimal": minimal_resume,
    "no-linkedin": no_linkedin_resume,
    "tricky": tricky_resume,
}


@pytest.mark.parametrize("name", RESUMES)
def test_dense_single_renders_exactly_like_its_golden_file(name: str, update_golden: bool) -> None:
    manifest = load_manifests(TEMPLATES)["dense-single"]
    tex = render(
        RESUMES[name](), manifest, manifest.typography_defaults, [], set(), templates_dir=TEMPLATES
    ).tex
    golden = GOLDEN / f"{name}.tex"

    if update_golden:
        GOLDEN.mkdir(parents=True, exist_ok=True)
        golden.write_text(tex, encoding="utf-8")
        return

    assert golden.exists(), (
        f"no golden file yet; run pytest --update-golden to create {golden.name}"
    )
    assert tex == golden.read_text(encoding="utf-8")
