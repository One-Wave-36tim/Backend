from fastapi import APIRouter

from app.schemas.health import HealthResponse
from app.services.health_service import get_health

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["헬스체크"],
    summary="헬스체크",
    description="서버 프로세스가 정상 동작 중인지 확인합니다.",
    response_description="헬스체크 결과",
)
def health() -> HealthResponse:
    # Controller stays thin: delegate to service
    return get_health()
