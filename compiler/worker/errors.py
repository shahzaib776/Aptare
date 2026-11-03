from typing import Any


class WorkerError(Exception):
    status_code = 500
    code = "internal_error"
    message = "Something went wrong in the compiler."

    def __init__(self, details: dict[str, Any] | None = None) -> None:
        super().__init__(self.message)
        self.details = details or {}


class CompileFailedError(WorkerError):
    status_code = 422
    code = "compile_failed"
    message = "The document did not compile."

    def __init__(self, log_tail: str) -> None:
        super().__init__({"log_tail": log_tail})


class CompileTimeoutError(WorkerError):
    status_code = 408
    code = "compile_timeout"
    message = "The document took too long to compile."


class NotReadyError(WorkerError):
    status_code = 503
    code = "compiler_not_ready"
    message = "Tectonic is not available or its package cache is empty."
