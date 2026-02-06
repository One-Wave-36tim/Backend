from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class PortfolioSourceType(str, Enum):
    NOTION = "notion"
    BLOG = "blog"
    PDF = "pdf"


class PortfolioUploadRequest(BaseModel):
    source_type: PortfolioSourceType
    source_url: str | None = Field(
        default=None, description="노션/블로그 URL (notion/blog인 경우 필수)"
    )


class PortfolioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    source_type: str
    source_url: str | None
    original_filename: str | None
    extracted_text: str
    extraction_status: str
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class PortfolioListResponse(BaseModel):
    portfolios: list[PortfolioResponse]
    total: int
