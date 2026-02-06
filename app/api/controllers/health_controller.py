from fastapi import APIRouter

from app.api.schemas.health import HealthResponse
from app.services.health_service import get_health

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    # Controller stays thin: delegate to service
    return get_health()
