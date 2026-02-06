from enum import Enum

from pydantic import BaseModel


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


class PortfolioListResponse(BaseModel):
    items: list[PortfolioResponse]
    total: int
