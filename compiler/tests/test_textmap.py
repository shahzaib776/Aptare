from tests.pdfs import make_pdf, open_pdf
from worker.models import Element
from worker.textmap import build_text_map, normalize


def el(id_: str, text: str) -> Element:
    return Element(id=id_, text=text)


def test_normalize_folds_ligatures_case_and_punctuation() -> None:
    assert normalize("ﬁnal Multi-Threaded, v2!") == "finalmultithreadedv2"


def test_single_line_element_gets_one_rect() -> None:
    doc = open_pdf(make_pdf([["Built a service", "that scales"]]))
    placements = build_text_map(doc, [el("a", "that scales")])["a"]
    assert len(placements) == 1
    assert placements[0].page == 0


def test_rect_covers_only_the_elements_words() -> None:
    doc = open_pdf(make_pdf([["Alpha Beta Gamma"]]))
    (whole,) = build_text_map(doc, [el("w", "Alpha Beta Gamma")])["w"]
    (middle,) = build_text_map(doc, [el("m", "Beta")])["m"]
    assert middle.rect[0] > whole.rect[0]
    assert middle.rect[2] < whole.rect[2]


def test_wrapped_element_gets_a_rect_per_line() -> None:
    doc = open_pdf(make_pdf([["Reduced the nightly build", "time by moving the cache"]]))
    placements = build_text_map(
        doc, [el("a", "Reduced the nightly build time by moving the cache")]
    )["a"]
    assert len(placements) == 2
    assert placements[0].rect[1] < placements[1].rect[1]


def test_hyphenated_line_break_still_matches() -> None:
    doc = open_pdf(make_pdf([["Built a multi-", "threaded crawler"]]))
    placements = build_text_map(doc, [el("a", "Built a multi-threaded crawler")])["a"]
    assert len(placements) == 2


def test_element_across_a_page_break_has_rects_on_both_pages() -> None:
    doc = open_pdf(make_pdf([["Led the migration of"], ["the billing platform"]]))
    placements = build_text_map(doc, [el("a", "Led the migration of the billing platform")])["a"]
    assert [p.page for p in placements] == [0, 1]


def test_identical_texts_match_in_document_order() -> None:
    doc = open_pdf(make_pdf([["Wrote tests", "Shipped fast", "Wrote tests"]]))
    result = build_text_map(doc, [el("first", "Wrote tests"), el("second", "Wrote tests")])
    assert result["first"][0].rect[1] < result["second"][0].rect[1]


def test_text_that_is_not_in_the_pdf_maps_to_nothing() -> None:
    doc = open_pdf(make_pdf([["Built a service"]]))
    assert build_text_map(doc, [el("a", "Something else entirely")]) == {"a": []}


def test_fallback_anchors_on_first_and_last_words() -> None:
    doc = open_pdf(
        make_pdf([["Led the migration of the old billing", "system to the new platform"]])
    )
    text = "Led the migration of the legacy billing system to the new platform"
    placements = build_text_map(doc, [el("a", text)])["a"]
    assert len(placements) == 2


def test_empty_text_maps_to_nothing() -> None:
    doc = open_pdf(make_pdf([["Built a service"]]))
    assert build_text_map(doc, [el("a", "...")]) == {"a": []}
