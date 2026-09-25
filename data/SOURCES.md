# Danh mục nguồn corpus

**Chủ đề:** Chatbot RAG hỗ trợ tra cứu thông tin du lịch và văn hóa tại Quần thể Di tích Cố đô Huế.

**Ngày thu thập:** 2026-09-20

## Tài liệu chính sách và quy định

| File landing | Tài liệu | Nguồn công khai |
| --- | --- | --- |
| `van_ban_hop_nhat_51_2026_luat_di_san_van_hoa.pdf` | Văn bản hợp nhất 51/VBHN-VPQH năm 2026: Luật Di sản văn hóa | [Cổng Thông tin điện tử Chính phủ](https://datafiles.chinhphu.vn/cpp/files/vbpq/2026/3/51-vbhn-vpqh.pdf) |
| `ke_hoach_275_2025_phat_trien_du_lich_hue.pdf` | Kế hoạch 275/KH-UBND: Phát triển du lịch, dịch vụ du lịch thành phố Huế giai đoạn 2025–2030, tầm nhìn đến năm 2045 | [Cổng TTĐT thành phố Huế](https://hue.gov.vn/Portals/0/Uploads/00.00.H57/Nam2025/Thang6/00.00.H57_275_KH_UBND_2025_PL1_signed.pdf) |
| `ke_hoach_188_2026_du_lich_sinh_thai_cong_dong_hue.pdf` | Kế hoạch 188/KH-UBND: Phát triển du lịch sinh thái, du lịch cộng đồng thành phố Huế giai đoạn 2026–2027 | [Cổng TTĐT thành phố Huế](https://hue.gov.vn/Portals/0/Uploads/VBPL/Nam2026/Thang4/00.00.H57-188-KH-UBND-2026-PL1_signed.pdf) |

Metadata tải xuống của các file trên được lưu tại `data/landing/legal/sources.json`.

## Bài viết và trang thông tin công khai

| File landing | Nội dung | Nguồn công khai |
| --- | --- | --- |
| `article_01.json` | Quần thể Di tích cố đô Huế | [Cục Di sản văn hóa](https://dsvh.gov.vn/quan-the-di-tich-co-do-hue-475) |
| `article_02.json` | Di tích lịch sử và kiến trúc nghệ thuật Quần thể kiến trúc Cố đô Huế | [Cục Di sản văn hóa](https://dsvh.gov.vn/di-tich-lich-su-va-kien-truc-nghe-thuat-quan-the-kien-truc-co-do-hue-2944) |
| `article_03.json` | Nhã nhạc - Âm nhạc cung đình Việt Nam | [Cục Di sản văn hóa](https://dsvh.gov.vn/nha-nhac-am-nhac-cung-dinh-viet-nam-483) |
| `article_04.json` | Ca Huế | [Cục Di sản văn hóa](https://dsvh.gov.vn/ca-hue-1180) |
| `article_05.json` | Thơ văn trên kiến trúc cung đình Huế | [Cục Di sản văn hóa](https://dsvh.gov.vn/tho-van-tren-kien-truc-cung-dinh-hue-1249) |

## Quy tắc tái lập

- Chạy lại `python -m src.task1_collect_legal_docs` để tải đúng ba PDF với tên ổn định.
- Chạy lại `python -m src.task2_crawl_news` để ghi đè đúng năm JSON, không tạo bản sao.
- Chạy lại `python -m src.task3_convert_markdown` để chuẩn hóa sang `data/standardized/legal/` và `data/standardized/news/`.
- Mỗi Markdown giữ `title`, `source`, thời điểm thu thập và `doc_type` trong front matter.
