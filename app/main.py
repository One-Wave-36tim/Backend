from fastapi import FastAPI

import app.db.entities as _entities  # noqa: F401
from app.db.session import Base, get_engine
from app.router import router

app = FastAPI(
    title="Backend",
    openapi_tags=[
        {"name": "헬스체크", "description": "서버 상태 확인 API"},
        {"name": "인증", "description": "로그인/회원가입/JWT 발급 API"},
        {"name": "홈", "description": "홈 화면 데이터 API"},
        {"name": "프로젝트", "description": "프로젝트/대시보드/포트폴리오 관리 API"},
        {"name": "루틴", "description": "홈 루틴 체크리스트 API"},
        {"name": "자소서", "description": "자소서 문단 작성 및 코치 API"},
        {"name": "심층인터뷰", "description": "심층 인터뷰 진행/가이드/인사이트 API"},
        {"name": "직무시뮬레이션", "description": "직무 시뮬레이션(v1 화면형) API"},
    ],
)
app.include_router(router)


@app.on_event("startup")
def init_db() -> None:
    Base.metadata.create_all(bind=get_engine())
