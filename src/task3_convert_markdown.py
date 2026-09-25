"""
Task 3 — Chuẩn hóa dữ liệu sang Markdown.

Hướng dẫn:
    1. Dùng MarkItDown để convert PDF/DOCX.
    2. Đọc JSON và giữ metadata ở đầu file Markdown.
    3. Giữ cấu trúc thư mục legal/ và news/.
    4. Không tạo file rỗng hoặc file trùng khi chạy lại.

Cài đặt:
    Dependency MarkItDown đã được khai báo trong pyproject.toml.
    
-> Hoặc dùng công cụ nào bạn quen khác Markitdown
"""

import json
from pathlib import Path


LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "standardized"


def convert_legal_docs() -> None:
    from markitdown import MarkItDown

    legal_dir = LANDING_DIR / "legal"
    output_dir = OUTPUT_DIR / "legal"
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = legal_dir / "sources.json"
    manifest = {}
    if manifest_path.exists():
        items = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest = {item["filename"]: item for item in items}

    converter = MarkItDown()
    for path in sorted(legal_dir.iterdir()):
        if path.suffix.lower() not in {".pdf", ".doc", ".docx"}:
            continue

        result = converter.convert(str(path))
        content = result.text_content.strip()
        if not content:
            raise ValueError(f"Converted document is empty: {path}")

        metadata = manifest.get(path.name, {})
        title = metadata.get("title", path.stem.replace("_", " ").title())
        header = (
            "---\n"
            f"title: {json.dumps(title, ensure_ascii=False)}\n"
            f"source: {json.dumps(metadata.get('url', str(path)), ensure_ascii=False)}\n"
            f"retrieved_at: {json.dumps(metadata.get('retrieved_at', ''), ensure_ascii=False)}\n"
            'doc_type: "legal"\n'
            "---\n\n"
        )
        output = output_dir / f"{path.stem}.md"
        output.write_text(header + content + "\n", encoding="utf-8")
        print(f"Saved: {output}")


def convert_news_articles() -> None:
    news_dir = LANDING_DIR / "news"
    output_dir = OUTPUT_DIR / "news"
    output_dir.mkdir(parents=True, exist_ok=True)
    required = {"url", "title", "date_crawled", "content_markdown"}

    for path in sorted(news_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        missing = required - data.keys()
        if missing:
            raise ValueError(f"{path} is missing metadata: {sorted(missing)}")

        content = str(data["content_markdown"]).strip()
        if not content:
            raise ValueError(f"Article content is empty: {path}")

        header = (
            "---\n"
            f"title: {json.dumps(data['title'], ensure_ascii=False)}\n"
            f"source: {json.dumps(data['url'], ensure_ascii=False)}\n"
            f"date_crawled: {json.dumps(data['date_crawled'], ensure_ascii=False)}\n"
            'doc_type: "news"\n'
            "---\n\n"
        )
        output = output_dir / f"{path.stem}.md"
        output.write_text(header + content + "\n", encoding="utf-8")
        print(f"Saved: {output}")


def convert_all() -> None:
    """Convert toàn bộ dữ liệu landing."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    convert_legal_docs()
    convert_news_articles()
    print(f"Saved Markdown to: {OUTPUT_DIR}")


if __name__ == "__main__":
    convert_all()
