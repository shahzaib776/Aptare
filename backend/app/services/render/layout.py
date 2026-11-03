from app.errors import AppError
from app.schemas.resume import SectionKey
from app.schemas.template import TemplateManifest
from app.schemas.typography import Typography


def check_layout(
    manifest: TemplateManifest, typography: Typography, section_order: list[SectionKey]
) -> None:
    """Reject what the renderer would silently accept: sizes out of bounds, a bad section order."""
    for name, (low, high) in manifest.typography_bounds.items():
        value = getattr(typography, name)
        if not low <= value <= high:
            raise AppError(
                "typography_out_of_bounds",
                f"{name} must be between {low} and {high}.",
                422,
                {"field": name, "allowed": [low, high], "given": value},
            )

    available = {section.key for section in manifest.sections}
    foreign = [key for key in section_order if key not in available]
    if foreign:
        raise AppError(
            "invalid_section_order",
            "The section order names sections this template does not have.",
            422,
            {"keys": foreign},
        )
    if len(section_order) != len(set(section_order)):
        raise AppError("invalid_section_order", "The section order lists a section twice.", 422)
