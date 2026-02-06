from __future__ import annotations

import re
from typing import Any

import httpx
from bs4 import BeautifulSoup
from notion_client import Client
from pypdf import PdfReader

class TextExtractor:
    def __init__(self, notion_api_key: str | None = None) -> None:
        self.notion_client: Client | None = (
            Client(auth=notion_api_key) if notion_api_key else None
        )

    async def extract_from_notion(self, notion_url: str) -> str:
        if not self.notion_client:
            raise ValueError("Notion API key is not configured")

        page_id = self._extract_notion_page_id(notion_url)
        
        # 페이지 정보 먼저 가져오기 (디버깅용)
        try:
            page = self.notion_client.pages.retrieve(page_id)
        except Exception as e:
            raise ValueError(f"Failed to retrieve Notion page: {str(e)}")
        
        # 재귀적으로 모든 블록 가져오기
        text_parts: list[str] = []
        await self._extract_blocks_recursive(page_id, text_parts)

        result = "\n".join(text_parts)
        
        # 빈 결과인 경우 경고
        if not result.strip():
            raise ValueError("No text content found in Notion page. Make sure the page has content and the integration has access.")
        
        return result

    async def extract_from_blog(self, blog_url: str) -> str:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(blog_url, follow_redirects=True)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
            tag.decompose()

        main_content = soup.find("main") or soup.find("article") or soup.find("body")
        text = (
            main_content.get_text(separator="\n", strip=True)
            if main_content
            else soup.get_text(separator="\n", strip=True)
        )
        return text

    async def extract_from_pdf(self, pdf_path: str) -> str:
        text_parts: list[str] = []
        with open(pdf_path, "rb") as file:
            reader = PdfReader(file)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)

        return "\n".join(text_parts)

    async def _extract_blocks_recursive(self, block_id: str, text_parts: list[str]) -> None:
        """재귀적으로 모든 블록을 탐색하여 텍스트 추출"""
        try:
            response = self.notion_client.blocks.children.list(block_id)
            blocks = response.get("results", [])
            
            for block in blocks:
                # 현재 블록에서 텍스트 추출
                text = self._extract_text_from_block(block)
                if text:
                    text_parts.append(text)
                
                # 블록에 자식이 있는 경우 재귀적으로 탐색
                block_type = block.get("type")
                has_children = block.get("has_children", False)
                
                if has_children:
                    child_block_id = block.get("id")
                    if child_block_id:
                        await self._extract_blocks_recursive(child_block_id, text_parts)
        except Exception as e:
            # 에러 발생 시 로그 남기고 계속 진행
            print(f"Error extracting blocks from {block_id}: {str(e)}")

    def _extract_notion_page_id(self, notion_url: str) -> str:
        """Notion URL에서 page_id 추출 (개선된 버전)"""
        # URL에서 UUID 형식의 page_id 추출
        # Notion URL 형식: https://www.notion.so/Page-Title-abc123def456... 또는
        # https://notion.so/workspace/Page-Title-abc123def456...
        
        # UUID 패턴: 32자리 hex (하이픈 포함/미포함)
        uuid_pattern = r'([a-f0-9]{32}|[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})'
        
        # URL에서 UUID 찾기
        match = re.search(uuid_pattern, notion_url, re.IGNORECASE)
        if match:
            page_id = match.group(1)
            # 하이픈이 없는 경우 추가
            if len(page_id) == 32:
                page_id = f"{page_id[:8]}-{page_id[8:12]}-{page_id[12:16]}-{page_id[16:20]}-{page_id[20:]}"
            return page_id
        
        # UUID를 찾지 못한 경우 기존 방식 시도
        parts = notion_url.split("-")
        if parts:
            last_part = parts[-1].split("?")[0].split("#")[0]
            # 32자리 hex인지 확인
            if len(last_part) == 32 and all(c in '0123456789abcdef' for c in last_part.lower()):
                return f"{last_part[:8]}-{last_part[8:12]}-{last_part[12:16]}-{last_part[16:20]}-{last_part[20:]}"
            return last_part
        
        raise ValueError(f"Invalid Notion URL format: {notion_url}")

    def _extract_text_from_block(self, block: dict[str, Any]) -> str:
        """블록에서 텍스트 추출 (더 많은 블록 타입 지원)"""
        block_type = block.get("type")
        
        # 지원하는 블록 타입들
        text_block_types = {
            "paragraph", "heading_1", "heading_2", "heading_3",
            "bulleted_list_item", "numbered_list_item", "to_do",
            "toggle", "quote", "callout", "code"
        }
        
        if block_type in text_block_types:
            block_data = block.get(block_type, {})
            rich_text = block_data.get("rich_text", [])
            text = "".join([rt.get("plain_text", "") for rt in rich_text])
            
            # 블록 타입에 따른 포맷팅
            if block_type == "heading_1":
                return f"# {text}\n"
            elif block_type == "heading_2":
                return f"## {text}\n"
            elif block_type == "heading_3":
                return f"### {text}\n"
            elif block_type == "bulleted_list_item":
                return f"- {text}\n"
            elif block_type == "numbered_list_item":
                return f"1. {text}\n"
            elif block_type == "to_do":
                checked = block_data.get("checked", False)
                checkbox = "[x]" if checked else "[ ]"
                return f"{checkbox} {text}\n"
            elif block_type == "quote":
                return f"> {text}\n"
            elif block_type == "code":
                language = block_data.get("language", "")
                code_text = block_data.get("rich_text", [])
                code = "".join([rt.get("plain_text", "") for rt in code_text])
                return f"```{language}\n{code}\n```\n"
            else:
                return f"{text}\n"
        
        return ""
