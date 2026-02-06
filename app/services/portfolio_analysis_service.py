from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.repositories.portfolio_analysis_repository import replace_portfolio_analysis
from app.db.repositories.portfolio_repository import find_portfolio_by_id
from app.schemas.portfolio import PortfolioAnalysisResponse
from app.services.portfolio_llm_service import call_gemini


def build_portfolio_analysis_prompt(extracted_text: str) -> str:
    return (
        "당신은 전문 채용 담당자이자 커리어 코치입니다. 아래 포트폴리오를 분석하여 "
        "사용자의 기술적 역량과 프로젝트 수행 능력을 파악하세요.\n\n"
        "포트폴리오 내용:\n"
        f"{extracted_text}\n\n"
        "다음 항목을 포함하여 분석 결과를 요약해 주세요:\n"
        "1. 프로젝트 핵심 요약: (어떤 문제를 해결했는가?)\n"
        "2. 기술적 강점: (도입한 기술이나 아키텍처의 특징)\n"
        "3. 논리적 공백 및 개선점: (설명이 부족하거나 의문이 생기는 지점)\n"
        "4. 심화 질문 추천 리스트: (면접에서 나올법한 날카로운 질문 3~5개)"
    )


def analyze_portfolio(db: Session, portfolio_id: int) -> PortfolioAnalysisResponse:
    portfolio = find_portfolio_by_id(db, portfolio_id)
    if not portfolio:
        raise ValueError("포트폴리오를 찾을 수 없습니다.")
    if not portfolio.extracted_text.strip():
        raise ValueError("포트폴리오 내용이 비어 있습니다.")

    settings = get_settings()
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY가 설정되어 있지 않습니다.")

    prompt = build_portfolio_analysis_prompt(portfolio.extracted_text)
    analysis_text = call_gemini(prompt, settings.gemini_model, settings.gemini_api_key)

    replace_portfolio_analysis(db, portfolio.id, analysis_text)
    return PortfolioAnalysisResponse(portfolio_id=portfolio.id, analysis=analysis_text)
