from app.schemas.base import StrictModel


class Typography(StrictModel):
    base_font_pt: float
    line_spread: float
    margin_in: float
    item_sep_pt: float
    section_sep_pt: float
