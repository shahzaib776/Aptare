"""Builds tiny PDFs with PyMuPDF so the PDF-reading code is tested without running LaTeX."""

import pymupdf

LEFT = 72.0
FONT_SIZE = 11.0
LEADING = 14.0


def make_pdf(pages: list[list[str]], *, first_baseline: float = 83.0) -> bytes:
    """One text line per string, `LEADING` points apart, starting at `first_baseline`."""
    doc = pymupdf.open()
    for lines in pages:
        page = doc.new_page(width=612, height=792)
        for i, text in enumerate(lines):
            page.insert_text(
                (LEFT, first_baseline + i * LEADING), text, fontsize=FONT_SIZE, fontname="helv"
            )
    data: bytes = doc.tobytes()
    return data


def make_pdf_at(baselines: list[float]) -> bytes:
    """A single page with one short line at each given baseline."""
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)
    for y in baselines:
        page.insert_text((LEFT, y), "text", fontsize=FONT_SIZE, fontname="helv")
    data: bytes = doc.tobytes()
    return data


def open_pdf(data: bytes) -> pymupdf.Document:
    return pymupdf.open(stream=data, filetype="pdf")
