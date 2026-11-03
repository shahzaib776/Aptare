from app.schemas.compile import Element
from app.schemas.resume import TailoredResume


def elements_from(visible: TailoredResume) -> list[Element]:
    """The text map's input: the summary, then every bullet, in the order the template prints them.

    The worker searches the PDF forwards, so this order must match the rendered order.
    """
    elements = [Element(id="summary", text=visible.summary)] if visible.summary else []
    for section in visible.sections:
        if section.key in ("experience", "projects"):
            for item in section.items:
                elements += [Element(id=str(b.id), text=b.text) for b in item.bullets]
    return elements
