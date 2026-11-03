import pytest

from tests.pdfs import make_pdf, make_pdf_at, open_pdf
from worker.metrics import last_page_fill, line_boxes


def test_fill_grows_with_content() -> None:
    short = last_page_fill(open_pdf(make_pdf_at([83.0])))
    half = last_page_fill(open_pdf(make_pdf_at([83.0, 400.0])))
    full = last_page_fill(open_pdf(make_pdf_at([83.0, 700.0])))
    assert short < 0.05
    assert half == pytest.approx(0.5, abs=0.06)
    assert 0.9 < full <= 1.0


def test_fill_uses_only_the_last_page() -> None:
    first_page_full_second_nearly_empty = make_pdf([["x"] * 40, ["tail"]])
    assert last_page_fill(open_pdf(first_page_full_second_nearly_empty)) < 0.05


def test_fill_of_a_blank_pdf_is_zero() -> None:
    assert last_page_fill(open_pdf(make_pdf([[]]))) == 0.0


def test_line_boxes_cover_every_line_in_reading_order() -> None:
    doc = open_pdf(make_pdf([["Built a service", "that scales"], ["Second page line"]]))
    boxes = line_boxes(doc)
    assert [b.chars for b in boxes] == [15, 11, 16]
    assert [b.page for b in boxes] == [0, 0, 1]
    assert boxes[0].rect[1] < boxes[1].rect[1]
    x0, y0, x1, y1 = boxes[0].rect
    assert x0 < x1 and y0 < y1


def test_line_boxes_of_a_blank_pdf_is_empty() -> None:
    assert line_boxes(open_pdf(make_pdf([[]]))) == []
