from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import CurrentUserId
from app.core.errors import NotFoundError
from app.db.session import get_db
from app.schemas.projects_v1 import (
    PortfolioCreateRequest,
    PortfolioCreateResponse,
    ProjectCreateV1Request,
    ProjectCreateV1Response,
    ProjectDashboardResponse,
    ProjectPortfolioPatchRequest,
    ProjectPortfolioPatchResponse,
    RoutineToggleRequest,
    RoutineToggleResponse,
)
from app.services.portfolio_crawl_service import crawl_blog_portfolios_background
from app.services.projects_v1_service import (
    create_portfolio_item_v1,
    create_project_v1,
    get_project_dashboard,
    patch_project_portfolio,
    pick_blog_portfolio_ids,
    toggle_routine_item,
)

router = APIRouter(prefix="/v1", tags=["프로젝트"])
routine_router = APIRouter(prefix="/v1", tags=["루틴"])


@router.post(
    "/projects",
    response_model=ProjectCreateV1Response,
    summary="지원 프로젝트 생성",
    description=(
        "회사/직무/마감일 기반으로 프로젝트를 생성하고 기본 공고 레코드를 함께 만듭니다. "
        "요청 본문에 `portfolio`를 포함하면 노션/블로그/PDF 링크와 "
        "대표 설명/개발자 모드/GitHub 정보를 "
        "프로젝트 귀속 포트폴리오로 동시 생성합니다."
    ),
    response_description="생성된 프로젝트 ID, 상태, 생성된 포트폴리오 ID 목록",
)
def create_project_endpoint(
    payload: ProjectCreateV1Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user_id: int = CurrentUserId,
) -> ProjectCreateV1Response:
    response = create_project_v1(db=db, user_id=user_id, payload=payload)
    blog_portfolio_ids = pick_blog_portfolio_ids(
        db=db,
        user_id=user_id,
        portfolio_ids=response.portfolioIds,
    )
    if blog_portfolio_ids:
        background_tasks.add_task(
            crawl_blog_portfolios_background,
            user_id,
            blog_portfolio_ids,
        )
    return response


@router.get(
    "/projects/{project_id}/dashboard",
    response_model=ProjectDashboardResponse,
    summary="프로젝트 상세 대시보드 조회",
    description="프로젝트 상세 화면에 필요한 자소서/모의면접/시뮬레이션 상태를 집계해 반환합니다.",
    response_description="프로젝트 상세 대시보드 데이터",
    responses={404: {"description": "프로젝트를 찾을 수 없음"}},
)
def get_project_dashboard_endpoint(
    project_id: UUID,
    db: Session = Depends(get_db),
    user_id: int = CurrentUserId,
) -> ProjectDashboardResponse:
    try:
        return get_project_dashboard(db=db, user_id=user_id, project_id=project_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/portfolios",
    response_model=PortfolioCreateResponse,
    summary="포트폴리오 추가",
    description="사용자가 수행한 포트폴리오 이력을 저장합니다. period는 YYYY-MM 형식입니다.",
    response_description="생성된 포트폴리오 ID",
)
def create_portfolio_endpoint(
    payload: PortfolioCreateRequest,
    db: Session = Depends(get_db),
    user_id: int = CurrentUserId,
) -> PortfolioCreateResponse:
    try:
        return create_portfolio_item_v1(db=db, user_id=user_id, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch(
    "/projects/{project_id}/portfolios/{portfolio_id}",
    response_model=ProjectPortfolioPatchResponse,
    summary="대표 포트폴리오 설정",
    description="프로젝트에 연결된 포트폴리오의 대표 여부를 변경합니다.",
    response_description="대표 설정 변경 결과",
    responses={404: {"description": "프로젝트 또는 포트폴리오를 찾을 수 없음"}},
)
def patch_project_portfolio_endpoint(
    project_id: UUID,
    portfolio_id: UUID,
    payload: ProjectPortfolioPatchRequest,
    db: Session = Depends(get_db),
    user_id: int = CurrentUserId,
) -> ProjectPortfolioPatchResponse:
    try:
        return patch_project_portfolio(
            db=db,
            user_id=user_id,
            project_id=project_id,
            portfolio_id=portfolio_id,
            is_representative=payload.isRepresentative,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@routine_router.patch(
    "/routines/items/{routine_item_id}",
    response_model=RoutineToggleResponse,
    summary="루틴 체크 토글",
    description="홈 화면 루틴 아이템의 체크 여부를 변경합니다.",
    response_description="루틴 변경 결과",
    responses={404: {"description": "루틴 아이템을 찾을 수 없음"}},
)
def patch_routine_endpoint(
    routine_item_id: UUID,
    payload: RoutineToggleRequest,
    db: Session = Depends(get_db),
    user_id: int = CurrentUserId,
) -> RoutineToggleResponse:
    try:
        return toggle_routine_item(
            db=db,
            user_id=user_id,
            routine_item_id=routine_item_id,
            checked=payload.checked,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
