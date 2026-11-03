import re
from typing import Any

from app.schemas.resume import TailoredResume

_SPECIAL = {
    "\\": r"\textbackslash{}",
    "{": r"\{",
    "}": r"\}",
    "$": r"\$",
    "&": r"\&",
    "#": r"\#",
    "^": r"\textasciicircum{}",
    "_": r"\_",
    "~": r"\textasciitilde{}",
    "%": r"\%",
}
_NORMALIZED = {
    "\u2013": "--",
    "\u2014": "---",
    "\u2018": "`",
    "\u2019": "'",
    "\u201c": "``",
    "\u201d": "''",
    "\u00a0": "~",
}
_REPLACEMENTS = _SPECIAL | _NORMALIZED
_PATTERN = re.compile("|".join(re.escape(char) for char in _REPLACEMENTS))


def escape_text(text: str) -> str:
    """Make plain text safe to place in a .tex file."""
    # TP-6: one pass over the input; chained replace() calls would re-escape their own output.
    return _PATTERN.sub(lambda match: _REPLACEMENTS[match.group()], text)


def _escape_value(value: Any) -> Any:
    if isinstance(value, str):
        return escape_text(value)
    if isinstance(value, list):
        return [_escape_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _escape_value(item) for key, item in value.items()}
    return value


def escape_resume(resume: TailoredResume) -> TailoredResume:
    """Return a copy of the resume with every text field escaped; call once, at the renderer."""
    # Every str is escaped, so a Literal field holding `_` or `&` would fail re-validation here.
    return TailoredResume.model_validate(_escape_value(resume.model_dump()))
