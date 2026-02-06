from pydantic import BaseModel


class PortfolioConversationTurn(BaseModel):
    role: str  # "assistant" or "user"
    content: str


class PortfolioQAItem(BaseModel):
    question: str | None = None
    answer: str | None = None


class PortfolioAnalysisResponse(BaseModel):
    portfolio_id: int
    analysis: str


class PortfolioQuestionsRequest(BaseModel):
    qa_conversation: list[PortfolioQAItem] = []
    stop_requested: bool = False


class PortfolioQuestionsResponse(BaseModel):
    portfolio_id: int
    message: str | None = None
    qa_item: PortfolioQAItem | None = None
