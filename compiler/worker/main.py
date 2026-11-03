import base64
import logging
import time
from typing import Any

import pymupdf
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from worker.errors import NotReadyError, WorkerError
from worker.metrics import last_page_fill, line_boxes
from worker.models import CompileRequest, CompileResponse
from worker.run_tectonic import compile_tex, is_ready
from worker.textmap import build_text_map

# Rule 13: the request holds resume text, so only codes and timings are ever logged.
log = logging.getLogger("compiler")


def _envelope(status: int, code: str, message: str, details: dict[str, Any]) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={"error": {"code": code, "message": message, "details": details}},
    )


def create_app() -> FastAPI:
    app = FastAPI(title="Aptare compiler")

    @app.exception_handler(WorkerError)
    async def worker_error(_: Request, exc: WorkerError) -> JSONResponse:
        log.warning("compile error code=%s", exc.code)
        return _envelope(exc.status_code, exc.code, exc.message, exc.details)

    @app.exception_handler(Exception)
    async def unexpected(_: Request, exc: Exception) -> JSONResponse:
        # Only the type is logged: the message could quote resume text (rule 13).
        log.error("unexpected error type=%s", type(exc).__name__)
        base = WorkerError()
        return _envelope(base.status_code, base.code, base.message, {})

    @app.exception_handler(RequestValidationError)
    async def invalid_request(_: Request, exc: RequestValidationError) -> JSONResponse:
        # pydantic's own errors repeat the offending input, which can be resume text.
        details = [{"loc": [str(p) for p in e["loc"]], "msg": e["msg"]} for e in exc.errors()]
        return _envelope(422, "invalid_request", "The request was not valid.", {"errors": details})

    @app.get("/health")
    def health() -> dict[str, str]:
        if not is_ready():
            raise NotReadyError
        return {"status": "ok"}

    @app.post("/compile")
    def compile_document(request: CompileRequest) -> CompileResponse:
        started = time.monotonic()
        pdf = compile_tex(request.tex, request.assets)
        with pymupdf.open(stream=pdf, filetype="pdf") as doc:
            response = CompileResponse(
                pdf=base64.b64encode(pdf).decode(),
                page_count=doc.page_count,
                last_page_fill=last_page_fill(doc),
                line_boxes=line_boxes(doc),
                text_map=build_text_map(doc, request.elements),
            )
        log.info("compiled pages=%d seconds=%.2f", response.page_count, time.monotonic() - started)
        return response

    return app
