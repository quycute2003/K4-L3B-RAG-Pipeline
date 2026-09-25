"""
Task 2 — Crawl bài viết/thông báo.

Hướng dẫn:
    1. Điền tối thiểu 5 URL công khai vào ARTICLE_URLS.
    2. Crawl từng URL bằng Crawl4AI.
    3. Lưu mỗi bài thành một JSON trong data/landing/news/.
    4. Giữ đủ url, title, date_crawled và content_markdown.

Cài browser trước khi chạy:
    python -m playwright install chromium
    
-> Dùng Firecrawl or bất cứ công cụ nào bạn quen    
"""

import asyncio
import json
from pathlib import Path


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"

ARTICLE_URLS = [
    "https://dsvh.gov.vn/quan-the-di-tich-co-do-hue-475",
    (
        "https://dsvh.gov.vn/di-tich-lich-su-va-kien-truc-nghe-thuat-"
        "quan-the-kien-truc-co-do-hue-2944"
    ),
    "https://dsvh.gov.vn/nha-nhac-am-nhac-cung-dinh-viet-nam-483",
    "https://dsvh.gov.vn/ca-hue-1180",
    "https://dsvh.gov.vn/tho-van-tren-kien-truc-cung-dinh-hue-1249",
]


async def crawl_article(url: str) -> dict:
    from datetime import datetime, timezone

    import requests
    from bs4 import BeautifulSoup
    from markdownify import markdownify

    def fetch() -> tuple[str, str]:
        response = requests.get(
            url,
            timeout=60,
            headers={"User-Agent": "Mozilla/5.0 (compatible; VinUni-RAG-Lab/1.0)"},
        )
        response.raise_for_status()
        response.encoding = response.apparent_encoding or response.encoding
        soup = BeautifulSoup(response.text, "html.parser")

        for element in soup.select("script, style, noscript, nav, footer, form"):
            element.decompose()

        content = (
            soup.select_one(".page-content")
            or soup.select_one("[itemprop='articleBody']")
            or soup.select_one("article")
            or soup.select_one("main")
        )
        if content is None:
            raise ValueError(f"Could not locate article body: {url}")

        heading = content.find("h1") or soup.find("h1")
        title_tag = soup.find("meta", property="og:title")
        title = (
            heading.get_text(" ", strip=True)
            if heading
            else title_tag.get("content", "").strip()
            if title_tag
            else soup.title.get_text(" ", strip=True)
            if soup.title
            else "Untitled"
        )
        return title, markdownify(str(content), heading_style="ATX").strip()

    title, markdown = await asyncio.to_thread(fetch)
    if len(markdown) < 200:
        raise ValueError(f"Crawled content is too short: {url}")

    return {
        "url": url,
        "title": title.strip(),
        "date_crawled": datetime.now(timezone.utc).isoformat(),
        "content_markdown": markdown,
    }


async def crawl_all() -> None:
    """Crawl và lưu từng bài thành một file JSON."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    for index, url in enumerate(ARTICLE_URLS, 1):
        try:
            article = await crawl_article(url)
            output = DATA_DIR / f"article_{index:02d}.json"
            output.write_text(
                json.dumps(article, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"Saved: {output}")
        except Exception as error:
            print(f"Failed: {url} - {error}")


if __name__ == "__main__":
    asyncio.run(crawl_all())
