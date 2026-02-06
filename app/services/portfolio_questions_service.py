import json
import re

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.repositories.portfolio_analysis_repository import find_latest_portfolio_analysis
from app.db.repositories.portfolio_repository import get_portfolio_by_id
from app.schemas.portfolio import (
    PortfolioConversationTurn,
    PortfolioQAItem,
    PortfolioQuestionsResponse,
)
from app.services.portfolio_llm_service import call_gemini


def build_portfolio_questions_prompt(
    portfolio_summary: str,
    conversation: list[PortfolioConversationTurn],
    stop_requested: bool,
) -> str:
    role_prompt = (
        "너는 사용자의 포트폴리오를 더 잘 이해하도록 돕는 인터뷰어다.\n"
        "포트폴리오 요약을 바탕으로 사용자가 스스로 의사결정과 맥락을 회고할 수 있게\n"
        "구체적인 질문을 던져라. 비판하지 말고 탐색/회고 중심으로 질문하라.\n"
        "한 번에 1~2개의 질문만 하며, 질문은 구체적이어야 한다.\n"
        "사용자가 '그만하기' 버튼을 누르면 즉시 질문 생성을 중단하고 종료 안내만 한다.\n"
    )

    conversation_text = (
        "\n".join(
            f"{'AI' if turn.role == 'assistant' else '사용자'}: {turn.content}"
            for turn in conversation
        )
        if conversation
        else "대화 없음"
    )

    base_prompt = (
        "[포트폴리오 요약]\n"
        f"{portfolio_summary}\n\n"
        "[대화 내용]\n"
        f"{conversation_text}\n\n"
        "[요청]\n"
        "위 포트폴리오 요약과 기존 대화를 참고해서, 사용자가 포트폴리오를 더 깊게 이해하도록\n"
        "유도 질문을 1개만 작성하라. 질문은 반드시 구체적이어야 하며, 포트폴리오의 맥락을\n"
        "되짚게 만드는 질문이어야 한다.\n"
        "사용자의 직전 답변을 고려해 꼬리질문을 해도 되고, 새로운 내용에 대한 질문도 가능하다.\n"
        "단, 사용자가 '그만하기' 버튼을 눌렀다면 질문을 만들지 말고 종료 문구만 출력하라.\n\n"
        "[출력형식]\n"
        "{\n"
        '  "question": "질문 한 개 또는 null",\n'
        '  "message": "종료 문구 또는 null"\n'
        "}\n"
        "반드시 JSON만 출력하고, 코드펜스(```)나 추가 텍스트는 금지한다.\n"
    )

    stop_line = f"stop_requested={str(stop_requested).lower()}\n"
    return role_prompt + stop_line + base_prompt


def generate_portfolio_questions(
    db: Session,
    portfolio_id: int,
    user_id: int,
    qa_conversation: list[PortfolioQAItem],
    stop_requested: bool,
) -> PortfolioQuestionsResponse:
    portfolio = get_portfolio_by_id(db=db, portfolio_id=portfolio_id, user_id=user_id)
    if not portfolio:
        raise ValueError("포트폴리오를 찾을 수 없습니다.")

    analysis = find_latest_portfolio_analysis(db, portfolio_id)
    if not analysis:
        raise ValueError("포트폴리오 분석 결과가 없습니다.")

    settings = get_settings()
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY가 설정되어 있지 않습니다.")

    if stop_requested:
        return PortfolioQuestionsResponse(
            portfolio_id=portfolio_id,
            message="대화를 종료할게요.",
            qa_item=None,
        )

    conversation: list[PortfolioConversationTurn] = []
    for item in qa_conversation:
        if item.question:
            conversation.append(PortfolioConversationTurn(role="assistant", content=item.question))
        if item.answer:
            conversation.append(PortfolioConversationTurn(role="user", content=item.answer))

    prompt = build_portfolio_questions_prompt(
        portfolio_summary=analysis.analysis_text,
        conversation=conversation,
        stop_requested=stop_requested,
    )
    model_output = call_gemini(prompt, settings.gemini_model, settings.gemini_api_key).strip()

    fenced_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", model_output, re.DOTALL)
    if fenced_match:
        model_output = fenced_match.group(1).strip()

    try:
        data = json.loads(model_output)
        question = data.get("question")
        message = data.get("message")
    except json.JSONDecodeError:
        question = model_output
        message = None

    if not question and message:
        return PortfolioQuestionsResponse(
            portfolio_id=portfolio_id, message=str(message), qa_item=None
        )

    qa_item = PortfolioQAItem(question=str(question) if question else None)
    return PortfolioQuestionsResponse(portfolio_id=portfolio_id, message=None, qa_item=qa_item)
