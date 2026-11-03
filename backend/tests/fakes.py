"""Test doubles shared across suites."""

from collections.abc import Callable
from dataclasses import dataclass

from app.schemas.compile import Element, Placement, WorkerResult


@dataclass
class Call:
    tex: str
    assets: dict[str, bytes]
    elements: list[Element]


class FakeCompiler:
    """Stands in for the compile worker: deterministic output, and it counts its calls."""

    def __init__(self) -> None:
        self.calls: list[Call] = []
        self.during_compile: Callable[[], None] | None = None
        self.error: Exception | None = None

    def compile(self, tex: str, assets: dict[str, bytes], elements: list[Element]) -> WorkerResult:
        self.calls.append(Call(tex, assets, elements))
        if self.during_compile:
            self.during_compile()
        if self.error:
            raise self.error
        return WorkerResult(
            pdf=b"%PDF-fake " + tex.encode(),
            page_count=1,
            last_page_fill=0.5,
            line_boxes=[],
            text_map={e.id: [Placement(page=0, rect=(0, 0, 1, 1))] for e in elements},
        )
