import pymupdf

from worker.models import LineBox


def line_boxes(doc: pymupdf.Document) -> list[LineBox]:
    """Every text line in the document in reading order (DESIGN 8.3 calibration, 8.5 widows)."""
    boxes: list[LineBox] = []
    for page in doc:
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                text = "".join(span["text"] for span in line["spans"]).strip()
                if text:
                    x0, y0, x1, y1 = line["bbox"]
                    boxes.append(LineBox(page=page.number, rect=(x0, y0, x1, y1), chars=len(text)))
    return boxes


def last_page_fill(doc: pymupdf.Document) -> float:
    """How full the last page is, 0 to 1 (DESIGN 8.5).

    The worker is not told the margins, so the top of the first text stands in for them: the
    usable area is the page height minus that margin at top and bottom. Approximate by design;
    the fit engine thresholds (85% / 25%) are coarse.
    """
    if doc.page_count == 0:
        return 0.0
    first_top = _text_extent(doc[0])
    last = _text_extent(doc[doc.page_count - 1])
    if first_top is None or last is None:
        return 0.0
    margin = first_top[0]
    usable = doc[0].rect.height - 2 * margin
    return float(max(0.0, min(1.0, (last[1] - margin) / usable)))


def _text_extent(page: pymupdf.Page) -> tuple[float, float] | None:
    """Top of the first and bottom of the last line of text on the page."""
    rects = [pymupdf.Rect(b[:4]) for b in page.get_text("blocks") if b[6] == 0]
    if not rects:
        return None
    return min(r.y0 for r in rects), max(r.y1 for r in rects)
