from fastapi import APIRouter

from ... import __version__
from ...services.runtime import get_runtime_status
from ..schemas import HealthResponse, RuntimeResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    runtime = get_runtime_status()
    return HealthResponse(
        status="ok" if runtime.available else "degraded",
        version=__version__,
        runtime=RuntimeResponse(
            available=runtime.available,
            description=runtime.description,
            detail=runtime.detail,
        ),
    )
