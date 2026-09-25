"""
Task 1 — Thu thập tài liệu chính sách/quy định.

Hướng dẫn:
    1. Chọn chủ đề của nhóm.
    2. Tìm tối thiểu 3 tài liệu PDF/DOCX từ nguồn công khai.
    3. Lưu file gốc vào data/landing/legal/.
    4. Đặt tên không dấu và thể hiện đúng nội dung.

Ví dụ tài liệu: học phí, học bổng, ký túc xá, quy trình đăng ký.
Nếu website chặn crawler, hãy chọn nguồn công khai khác; không vượt WAF.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import requests


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"

LEGAL_SOURCES = [
    {
        "filename": "van_ban_hop_nhat_51_2026_luat_di_san_van_hoa.pdf",
        "title": (
            "Văn bản hợp nhất 51/VBHN-VPQH năm 2026: Luật Di sản văn hóa"
        ),
        "url": (
            "https://datafiles.chinhphu.vn/cpp/files/vbpq/2026/3/"
            "51-vbhn-vpqh.pdf"
        ),
    },
    {
        "filename": "ke_hoach_275_2025_phat_trien_du_lich_hue.pdf",
        "title": (
            "Kế hoạch 275/KH-UBND: Phát triển du lịch, dịch vụ du lịch "
            "thành phố Huế giai đoạn 2025–2030, tầm nhìn đến năm 2045"
        ),
        "url": (
            "https://hue.gov.vn/Portals/0/Uploads/00.00.H57/Nam2025/Thang6/"
            "00.00.H57_275_KH_UBND_2025_PL1_signed.pdf"
        ),
    },
    {
        "filename": "ke_hoach_188_2026_du_lich_sinh_thai_cong_dong_hue.pdf",
        "title": (
            "Kế hoạch 188/KH-UBND: Phát triển du lịch sinh thái, du lịch "
            "cộng đồng thành phố Huế giai đoạn 2026–2027"
        ),
        "url": (
            "https://hue.gov.vn/Portals/0/Uploads/VBPL/Nam2026/Thang4/"
            "00.00.H57-188-KH-UBND-2026-PL1_signed.pdf"
        ),
    },
]


def setup_directory() -> None:
    """Tạo thư mục lưu tài liệu gốc."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Ready: {DATA_DIR}")


def download_documents() -> None:
    """Tải ít nhất 3 PDF/DOCX từ nguồn công khai."""
    retrieved_at = datetime.now(timezone.utc).isoformat()
    manifest = []

    for source in LEGAL_SOURCES:
        response = requests.get(
            source["url"],
            timeout=60,
            headers={"User-Agent": "Mozilla/5.0 (compatible; VinUni-RAG-Lab/1.0)"},
        )
        response.raise_for_status()
        content = response.content
        if len(content) <= 1024 or not content.startswith(b"%PDF"):
            raise ValueError(f"Downloaded file is not a valid PDF: {source['url']}")

        output = DATA_DIR / source["filename"]
        output.write_bytes(content)
        manifest.append({**source, "retrieved_at": retrieved_at})
        print(f"Saved: {output}")

    (DATA_DIR / "sources.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    setup_directory()
    download_documents()
