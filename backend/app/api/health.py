from typing import Annotated

import httpx
from fastapi import APIRouter, Depends

from app.config import Settings
from app.deps import get_settings
from app.schemas.health import HealthResponse

router = APIRouter()

_PROBE_TIMEOUT_SECONDS = 1.0


def compiler_reachable(url: str, transport: httpx.BaseTransport | None = None) -> bool:
    try:
        with httpx.Client(transport=transport, timeout=_PROBE_TIMEOUT_SECONDS) as client:
            return client.get(f"{url}/health").is_success
    except httpx.HTTPError:
        return False


@router.get("/health")
def health(settings: Annotated[Settings, Depends(get_settings)]) -> HealthResponse:
    """Liveness, plus whether the compile worker answers."""
    reachable = compiler_reachable(settings.compiler_url)
    return HealthResponse(status="ok", compiler="ok" if reachable else "unreachable")
