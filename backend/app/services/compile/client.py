import base64
import binascii
import logging
from typing import Any, Protocol

import httpx
from pydantic import ValidationError

from app.errors import AppError
from app.schemas.base import StrictModel
from app.schemas.compile import Element, LineBox, Placement, WorkerResult

logger = logging.getLogger(__name__)

# The worker itself gives up after 10 s (rule 12); the rest is Tectonic start-up and transfer.
_TIMEOUT_SECONDS = 20.0

# worker error code -> (API error code, HTTP status, message)
_WORKER_ERRORS = {
    "compile_failed": ("compile_failed", 422, "The resume did not compile."),
    "compile_timeout": ("compile_timeout", 504, "The resume took too long to compile."),
    "compiler_not_ready": ("compiler_unavailable", 503, "The compiler is not ready yet."),
}


class Compiler(Protocol):
    def compile(
        self, tex: str, assets: dict[str, bytes], elements: list[Element]
    ) -> WorkerResult: ...


class _Reply(StrictModel):
    pdf: str
    page_count: int
    last_page_fill: float
    line_boxes: list[LineBox]
    text_map: dict[str, list[Placement]]


def _compiler_error() -> AppError:
    return AppError("compiler_error", "The compiler gave an unexpected reply.", 502)


class CompilerClient:
    """HTTP client for the compile worker (`compiler/`)."""

    def __init__(self, base_url: str, transport: httpx.BaseTransport | None = None) -> None:
        self._base_url = base_url
        self._transport = transport

    def compile(self, tex: str, assets: dict[str, bytes], elements: list[Element]) -> WorkerResult:
        """Compile `tex`; `elements` must be in render order. Raises `AppError` on any failure."""
        payload = {
            "tex": tex,
            "assets": {name: base64.b64encode(data).decode() for name, data in assets.items()},
            "elements": [e.model_dump() for e in elements],
        }
        try:
            with httpx.Client(transport=self._transport, timeout=_TIMEOUT_SECONDS) as http:
                response = http.post(f"{self._base_url}/compile", json=payload)
        except httpx.HTTPError as error:
            # The address and error type say what is misconfigured; httpx errors never carry the
            # request body, so no resume text can reach the log (rule 13).
            logger.warning(
                "Cannot reach the compiler at %s (%s)", self._base_url, type(error).__name__
            )
            raise AppError("compiler_unavailable", "The compiler cannot be reached.", 503) from None
        if response.is_success:
            return _parse(response)
        raise _error_from(response)


def _parse(response: httpx.Response) -> WorkerResult:
    # Rule 13: validation errors quote their input, so none of them is chained or logged.
    try:
        reply = _Reply.model_validate_json(response.content)
        pdf = base64.b64decode(reply.pdf, validate=True)
    except (ValidationError, binascii.Error):
        raise _compiler_error() from None
    return WorkerResult(**{**reply.model_dump(), "pdf": pdf})


def _error_from(response: httpx.Response) -> AppError:
    try:
        error: dict[str, Any] = response.json()["error"]
        code, status, message = _WORKER_ERRORS[error["code"]]
    except (ValueError, KeyError, TypeError):
        return _compiler_error()
    details = error.get("details") if code == "compile_failed" else None
    return AppError(code, message, status, details)
