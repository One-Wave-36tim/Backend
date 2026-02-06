from fastapi import APIRouter

from app.controllers.auth_controller import router as auth_router
from app.controllers.health_controller import router as health_router
from app.controllers.portfolio_controller import router as portfolio_router
from app.controllers.simulation_controller import router as simulation_router
from app.controllers.user_settings_controller import router as user_settings_router
from app.controllers.signup_controller import router as signup_router

router = APIRouter()
router.include_router(health_router)
router.include_router(auth_router)
router.include_router(portfolio_router)
router.include_router(simulation_router)
router.include_router(user_settings_router)
router.include_router(signup_router)
