from fastapi import APIRouter

from app.controllers.auth_controller import router as auth_router
from app.controllers.deep_interview_controller import (
    insight_router as deep_interview_insight_router,
)
from app.controllers.deep_interview_controller import router as deep_interview_router
from app.controllers.health_controller import router as health_router
from app.controllers.home_v1_controller import router as home_v1_router
from app.controllers.projects_v1_controller import router as projects_v1_router
from app.controllers.projects_v1_controller import routine_router as routine_v1_router
from app.controllers.resume_v1_controller import router as resume_v1_router
from app.controllers.signup_controller import router as signup_router
from app.controllers.simulation_v1_controller import router as simulation_v1_router

router = APIRouter()
router.include_router(health_router)
router.include_router(auth_router)
router.include_router(home_v1_router)
router.include_router(projects_v1_router)
router.include_router(routine_v1_router)
router.include_router(resume_v1_router)
router.include_router(deep_interview_router)
router.include_router(deep_interview_insight_router)
router.include_router(simulation_v1_router)
router.include_router(signup_router)
