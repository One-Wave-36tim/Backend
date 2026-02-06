from app.schemas.health import HealthResponse


def get_health() -> HealthResponse:
    return HealthResponse(ok=True)
