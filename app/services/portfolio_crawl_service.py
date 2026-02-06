from __future__ import annotations

import re
from datetime import UTC, datetime
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from app.db.repositories.portfolio_repository import (
    get_portfolios_by_ids,
    mark_portfolio_crawl_failed,
    update_portfolio_extracted_text,
)
from app.db.session import get_session_local

_MAX_TEXT_LENGTH = 20000


def _is_http_url(value: str | None) -> bool:
    if not value:
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _normalize_text(text: str) -> str:
    compact = re.sub(r"[ \t]+", " ", text)
    compact = re.sub(r"\n{3,}", "\n\n", compact)
    return compact.strip()


def _extract_text_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    normalized = _normalize_text(text)
    return normalized[:_MAX_TEXT_LENGTH]


def _crawl_blog_text(url: str) -> str:
    with httpx.Client(
        timeout=20,
        follow_redirects=True,
        headers={"User-Agent": "Mozilla/5.0 (compatible; GDGHackertonBot/1.0)"},
    ) as client:
        response = client.get(url)
        response.raise_for_status()
        return _extract_text_from_html(response.text)


def crawl_blog_portfolios_background(user_id: int, portfolio_ids: list[int]) -> None:
    session_local = get_session_local()
    db = session_local()
    try:
        rows = get_portfolios_by_ids(db=db, user_id=user_id, portfolio_ids=portfolio_ids)
        for row in rows:
            if row.source_type != "blog":
                continue
            if not _is_http_url(row.source_url):
                mark_portfolio_crawl_failed(db=db, portfolio=row, reason="invalid blog url")
                continue
            try:
                text = _crawl_blog_text(row.source_url)
                update_portfolio_extracted_text(
                    db=db,
                    portfolio=row,
                    extracted_text=text,
                    meta_patch={
                        "crawlStatus": "SUCCESS",
                        "crawlUpdatedAt": datetime.now(tz=UTC).isoformat(),
                        "crawlSource": "blog",
                        "crawlTextLength": len(text),
                    },
                )
            except Exception as exc:
                mark_portfolio_crawl_failed(db=db, portfolio=row, reason=str(exc))
    finally:
        db.close()
