from fastapi import APIRouter

from app.controllers.auth_controller import router as auth_router
from app.controllers.health_controller import router as health_router

router = APIRouter()
router.include_router(health_router)
router.include_router(auth_router)
