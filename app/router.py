from fastapi import APIRouter

from app.controllers.auth_controller import router as auth_router
from app.controllers.health_controller import router as health_router
from app.controllers.portfolio_analysis_controller import router as portfolio_analysis_router
from app.controllers.portfolio_questions_controller import router as portfolio_questions_router

router = APIRouter()
router.include_router(health_router)
router.include_router(auth_router)
router.include_router(portfolio_analysis_router)
router.include_router(portfolio_questions_router)
