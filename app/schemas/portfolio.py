from enum import Enum

from pydantic import BaseModel, Field


class PortfolioConversationTurn(BaseModel):
    role: str
    content: str


class PortfolioQAItem(BaseModel):
    question: str | None = None
    answer: str | None = None


class PortfolioAnalysisResponse(BaseModel):
    portfolio_id: int
    analysis: str


class PortfolioQuestionsRequest(BaseModel):
    qa_conversation: list[PortfolioQAItem] = Field(default_factory=list)
    stop_requested: bool = False


class PortfolioQuestionsResponse(BaseModel):
    portfolio_id: int
    message: str | None = None
    qa_item: PortfolioQAItem | None = None


class PortfolioSourceType(str, Enum):
    NOTION = "notion"
    BLOG = "blog"
    PDF = "pdf"


class PortfolioResponse(BaseModel):
    id: int
    user_id: int
    source_type: PortfolioSourceType
    source_url: str | None = None
    filename: str | None = None
    extracted_text: str = ""
    is_representative: bool = False
    meta: dict | None = None


class PortfolioListResponse(BaseModel):
    items: list[PortfolioResponse]
    total: int