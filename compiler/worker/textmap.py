import unicodedata
from dataclasses import dataclass

import pymupdf

from worker.models import Element, Placement

# Fallback anchors: how many words at each end of an element must match.
ANCHOR_WORDS = 3


def normalize(text: str) -> str:
    """Letters and digits only, lowercased, ligatures expanded.

    Line wraps, hyphenation and spacing all disappear, so wrapped text matches wherever the
    typesetter broke it.
    """
    folded = unicodedata.normalize("NFKC", text).lower()
    return "".join(c for c in folded if c.isalnum())


def build_text_map(doc: pymupdf.Document, elements: list[Element]) -> dict[str, list[Placement]]:
    """Find each element in the PDF; `elements` must be in render order (DESIGN 8.6, rule 8)."""
    words = _words(doc)
    haystack = "".join(normalize(w.text) for w in words)
    owner = [i for i, w in enumerate(words) for _ in normalize(w.text)]
    cursor = 0
    result: dict[str, list[Placement]] = {}
    for element in elements:
        span = _find(haystack, cursor, element.text)
        if span is None:
            result[element.id] = []
            continue
        start, end = span
        cursor = end
        result[element.id] = _line_rects(words[owner[start] : owner[end - 1] + 1])
    return result


@dataclass(frozen=True)
class _Word:
    page: int
    line_key: tuple[int, int, int]
    rect: pymupdf.Rect
    text: str


def _words(doc: pymupdf.Document) -> list[_Word]:
    return [
        _Word(page.number, (page.number, block, line), pymupdf.Rect(x0, y0, x1, y1), text)
        for page in doc
        for x0, y0, x1, y1, text, block, line, _ in page.get_text("words")
        if normalize(text)
    ]


def _find(haystack: str, cursor: int, text: str) -> tuple[int, int] | None:
    needle = normalize(text)
    if not needle:
        return None
    start = haystack.find(needle, cursor)
    if start != -1:
        return start, start + len(needle)
    return _find_by_anchors(haystack, cursor, text)


def _find_by_anchors(haystack: str, cursor: int, text: str) -> tuple[int, int] | None:
    """Match the first and last few words when the middle differs (DESIGN 8.6 fallback)."""
    tokens = [t for t in (normalize(w) for w in text.split()) if t]
    if len(tokens) <= 2 * ANCHOR_WORDS:
        return None
    head = "".join(tokens[:ANCHOR_WORDS])
    tail = "".join(tokens[-ANCHOR_WORDS:])
    start = haystack.find(head, cursor)
    if start == -1:
        return None
    tail_start = haystack.find(tail, start + len(head))
    if tail_start == -1:
        return None
    return start, tail_start + len(tail)


def _line_rects(words: list[_Word]) -> list[Placement]:
    """One rectangle per rendered line, covering only the matched words on it."""
    placements: list[Placement] = []
    current: pymupdf.Rect | None = None
    key = None
    page = 0
    for word in words:
        if word.line_key != key and current is not None:
            placements.append(_placement(page, current))
            current = None
        if current is None:
            current = pymupdf.Rect(word.rect)
        else:
            current |= word.rect
        key, page = word.line_key, word.page
    if current is not None:
        placements.append(_placement(page, current))
    return placements


def _placement(page: int, rect: pymupdf.Rect) -> Placement:
    return Placement(page=page, rect=(rect.x0, rect.y0, rect.x1, rect.y1))
