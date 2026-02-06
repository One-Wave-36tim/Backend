from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.db.entities.user import User
    from app.db.entities.portfolio_analysis import PortfolioAnalysis


class PortfolioSourceType(str, Enum):
    NOTION = "notion"
    BLOG = "blog"
    PDF = "pdf"

    @classmethod
    def _missing_(cls, value: object) -> "PortfolioSourceType | None":
        if isinstance(value, str):
            normalized = value.lower()
            for member in cls:
                if member.value == normalized or member.name.lower() == normalized:
                    return member
        return None


class ExtractionStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class Portfolio(Base):
    __tablename__ = "portfolios"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_type: Mapped[PortfolioSourceType] = mapped_column(
        SAEnum(
            PortfolioSourceType,
            name="portfolio_source_type",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    original_filename: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False)
    extraction_status: Mapped[ExtractionStatus] = mapped_column(
        String(20), default=ExtractionStatus.PENDING.value, nullable=False
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="portfolios")
    analyses: Mapped[list["PortfolioAnalysis"]] = relationship(
        "PortfolioAnalysis", back_populates="portfolio", cascade="all, delete-orphan"
    )
