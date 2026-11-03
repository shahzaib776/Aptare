"""Real Tectonic compiles; run in the image with no network: `make test-compile`."""

import contextlib
import os
import re
import time
from pathlib import Path

import pytest

from tests.pdfs import open_pdf
from worker.errors import CompileFailedError, CompileTimeoutError
from worker.metrics import line_boxes
from worker.models import Element
from worker.run_tectonic import TIMEOUT_SECONDS, compile_tex
from worker.textmap import build_text_map, normalize

pytestmark = pytest.mark.compile

GOLDEN = Path(
    os.environ.get("GOLDEN_DIR", Path(__file__).resolve().parents[2] / "backend/tests/golden")
)
GOLDEN_DENSE = GOLDEN if (GOLDEN / "full.tex").exists() else GOLDEN / "dense-single"
NAMES = ["full", "minimal", "no-linkedin", "tricky"]
ITEM = re.compile(r"^\s*\\resumeItem\{(.*)\}$", re.MULTILINE)


def golden_tex(name: str) -> str:
    return (GOLDEN_DENSE / f"{name}.tex").read_text(encoding="utf-8")


def bullets(tex: str) -> list[str]:
    return ITEM.findall(tex)


def document(body: str) -> str:
    # Same class options as the template: the offline cache only holds what warmup.tex used.
    head = "\\documentclass[letterpaper,11pt]{article}\n\\begin{document}\n"
    return head + body + "\n\\end{document}\n"


def pdf_text(pdf: bytes) -> str:
    with open_pdf(pdf) as doc:
        return "".join(page.get_text() for page in doc)


@pytest.mark.parametrize("name", NAMES)
def test_golden_documents_compile_to_one_page(name: str) -> None:
    with open_pdf(compile_tex(golden_tex(name), {})) as doc:
        assert doc.page_count == 1


def test_every_bullet_is_extractable_in_order() -> None:
    """TP-8: ATS parsers read the text layer, so each bullet must come out of the PDF."""
    tex = golden_tex("full")
    text = normalize(pdf_text(compile_tex(tex, {})))
    cursor = 0
    for bullet in bullets(tex):
        found = text.find(normalize(bullet), cursor)
        assert found != -1, bullet
        cursor = found


def test_same_input_gives_the_same_bytes() -> None:
    tex = golden_tex("full")
    assert compile_tex(tex, {}) == compile_tex(tex, {})


def test_text_map_finds_wrapped_hyphenated_bullets() -> None:
    # Plain text, as the backend sends it: same bullets as tricky_resume() in backend/tests.
    plain = [
        "Cut R&D costs 30% using C# & $5k_budget ~ 2^3 {braces}",
        "Designed a multi-threaded, fault-tolerant ingestion pipeline processing millions of "
        "records per day across several regions, cutting end-to-end latency for downstream "
        "analytics consumers",
    ]
    elements = [Element(id=f"b{i}", text=t) for i, t in enumerate(plain)]
    with open_pdf(compile_tex(golden_tex("tricky"), {})) as doc:
        mapped = build_text_map(doc, elements)
    assert mapped["b0"]
    assert len(mapped["b1"]) >= 2, "the long bullet should wrap onto at least two lines"


def test_line_boxes_describe_the_rendered_lines() -> None:
    with open_pdf(compile_tex(golden_tex("full"), {})) as doc:
        boxes = line_boxes(doc)
    assert len(boxes) > 10
    assert all(b.chars > 0 for b in boxes)


def test_special_characters_in_links_survive() -> None:
    """Parked since step 4: URL escaping inside \\href."""
    with open_pdf(compile_tex(golden_tex("tricky"), {})) as doc:
        uris = {link.get("uri") for page in doc for link in page.get_links()}
    assert "https://site.com/~ada_x?a=1%202#top" in uris


def test_blank_lines_inside_arguments_compile() -> None:
    """Parked since step 4: a paragraph break inside a macro argument."""
    text = pdf_text(compile_tex(golden_tex("tricky"), {}))
    assert "Engineer" in text and "Lead" in text


def test_escaped_input_command_is_just_text() -> None:
    text = pdf_text(compile_tex(document(r"\textbackslash{}input\{/etc/passwd\}"), {}))
    assert "input{/etc/passwd}" in text.replace("\n", "")


@pytest.mark.xfail(
    strict=True,
    reason="Tectonic 0.17 --untrusted does not stop \\input of files outside the work "
    "directory. Fine while templates are committed and user text is escaped; user-uploaded "
    "templates (TP-9) need per-compile isolation first. Flips to a failure when fixed.",
)
def test_raw_input_of_a_system_file_is_blocked() -> None:
    try:
        pdf_or_log = pdf_text(compile_tex(document(r"\input{/etc/passwd}"), {}))
    except CompileFailedError as error:
        pdf_or_log = error.details["log_tail"]
    assert "nologin" not in pdf_or_log


def test_shell_escape_does_nothing(tmp_path: Path) -> None:
    marker = tmp_path / "pwned"
    with contextlib.suppress(CompileFailedError):
        compile_tex(document(rf"\immediate\write18{{touch {marker}}}"), {})
    assert not marker.exists()


def test_writing_outside_the_work_directory_is_blocked(tmp_path: Path) -> None:
    target = tmp_path / "written"
    body = rf"\immediate\openout3={target}\immediate\write3{{x}}\immediate\closeout3"
    with contextlib.suppress(CompileFailedError):
        compile_tex(document(body), {})
    assert not target.exists()


def test_an_endless_loop_times_out() -> None:
    started = time.monotonic()
    with pytest.raises(CompileTimeoutError):
        compile_tex(document(r"\def\a{\a}\a"), {})
    assert time.monotonic() - started < TIMEOUT_SECONDS + 3


def test_a_broken_document_reports_the_log() -> None:
    with pytest.raises(CompileFailedError) as raised:
        compile_tex(document(r"\undefinedcommand"), {})
    assert "undefined" in raised.value.details["log_tail"].lower()


def test_assets_are_available_to_the_document() -> None:
    sub = r"\textbf{from-an-asset}"
    pdf = compile_tex(document(r"\input{parts/body.tex}"), {"parts/body.tex": sub.encode()})
    assert "from-an-asset" in pdf_text(pdf)
