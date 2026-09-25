# Báo cáo đóng góp cá nhân — Nguyễn Minh Thịnh

## Thông tin

- Họ và tên: Nguyễn Minh Thịnh
- Mã học viên: 2A202602556
- Nhóm: DeltaX, lớp K4-L3B
- Repository/branch: `K4-L3B-RAG-Pipeline` / `feat/generation-ui` (đã merge vào `main`)

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit | Trạng thái |
| --- | --- | --- | --- |
| Task 8 — PageIndex fallback | Đọc key từ môi trường, tạo PDF tạm cho bài viết, upload PDF, cache document ID, giới hạn thời gian chờ và chuyển đoạn tìm được về `SearchResult` giữ nguồn | `src/task8_pageindex_vectorless.py`, `e0146d1` | Code xong; chưa kiểm chứng với dịch vụ thật vì chưa có `PAGEINDEX_API_KEY` |
| Task 9 — Retrieval pipeline | Nối dense và BM25, gọi RRF một lần, so ngưỡng bằng cosine score gốc của dense, giữ kết quả hybrid khi fallback không khả dụng | `src/task9_retrieval_pipeline.py`, `e0146d1` | Code và contract test xong; ngưỡng thực nghiệm đang chờ index cục bộ |
| Task 10 — Generation có citation | Sắp xếp context mà không sửa danh sách đầu vào, gắn nhãn nguồn, gọi provider được chọn, ánh xạ citation về đúng chunk và từ chối khi không có bằng chứng/citation hợp lệ | `src/task10_generation.py`, `e0146d1` | Code và test giả lập xong; chưa thử LLM thật vì `.env` chưa có model/key |
| Giao diện | Hiển thị câu trả lời, link nguồn, retrieval method, score và lưu nguồn trong lịch sử chat | `app.py`, `e0146d1` | Code xong; demo end-to-end đang chờ cấu hình và index |
| Kiểm thử | Bổ sung test offline cho citation sau khi đổi thứ tự context, safe refusal, parse kết quả PageIndex và cache upload | `tests/test_generation_ui_pipeline.py`, `e0146d1` | Done |

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Dùng điểm cosine từ dense search để quyết định fallback, sau đó mới dùng PageIndex khi điểm dưới ngưỡng; nếu PageIndex lỗi thì giữ kết quả hybrid.
   **Lý do/evidence:** RRF và cosine có thang điểm khác nhau. Contract test `test_retrieve_uses_dense_score_for_fallback`, `test_retrieve_fuses_once_when_dense_is_confident` và `test_retrieve_survives_fallback_provider_error` kiểm tra ba nhánh này.
   **Trade-off:** Ngưỡng `0.3` hiện là mặc định của code, chưa phải ngưỡng đã được hiệu chỉnh trên truy vấn Huế; PageIndex cần key, index và thời gian xử lý riêng.

2. **Quyết định:** Buộc câu trả lời có nhãn citation dạng `[n]` khớp với `sources`; nếu nhãn thiếu hoặc trỏ đến nguồn không tồn tại thì trả safe refusal.
   **Lý do/evidence:** Test `test_generation_citations_follow_sources_after_reordering` và `test_generation_refuses_missing_or_invented_citation` xác nhận citation được ánh xạ lại sau khi đổi thứ tự context.
   **Trade-off:** Câu trả lời đúng nhưng không tuân đúng định dạng `[n]` cũng bị từ chối; cần thử với LLM thật để xem prompt có tạo đúng định dạng ổn định hay không.

## Kiểm thử và kết quả

- Môi trường kiểm thử: `.venv` Python 3.13.15, cài dependency bằng `pip install -e ".[dev]"`.
- Chạy `python -m pytest tests/test_contracts.py tests/test_generation_ui_pipeline.py -q -p no:cacheprovider`: **19/19 pass**.
- Chạy `python -m pytest tests/test_acceptance.py -q -p no:cacheprovider`: **3 pass, 2 fail**. Hai lỗi thuộc artifact evaluation của nhóm: `golden_dataset.json` hiện rỗng và `group_project/evaluation/RESULT.md` còn `TODO`.
- Câu hỏi đúng domain chuẩn bị cho demo: “Nhã nhạc được UNESCO công nhận vào ngày nào?”; bằng chứng ở `data/standardized/news/article_03.md`, dẫn về bài “Nhã nhạc - Âm nhạc cung đình Việt Nam” trong `data/SOURCES.md`.
- Đối chiếu landing và standardized của `article_03`: JSON có đủ bốn metadata bắt buộc, URL là `https://dsvh.gov.vn/nha-nhac-am-nhac-cung-dinh-viet-nam-483`; ba đoạn nội dung mẫu trong `content_markdown` vẫn xuất hiện trong Markdown chuẩn hóa. Đây là kiểm tra bảo toàn nội dung giữa hai tầng dữ liệu, chưa phải đánh giá toàn bộ nguồn.
- Câu hỏi ngoài domain chuẩn bị cho demo: “Ai vô địch World Cup 2022?”; corpus Huế không chứa bằng chứng cho câu này, nên kết quả mong đợi là từ chối xác minh.
- Thử BM25 trực tiếp trên corpus hiện có (`lexical_search(..., top_k=3)`): câu Nhã nhạc xếp `news/article_03::chunk-0010` đầu tiên (score `37.072`); câu World Cup vẫn trả đoạn không liên quan, ví dụ `news/article_03::chunk-0014` (score `8.575`). Đây là lý do cần kiểm tra dense score và safe refusal; BM25 score không dùng để đặt ngưỡng fallback.
- Kiểm tra chuyển bài viết sang PDF cho PageIndex bằng Chrome headless có sẵn trên máy: `news/article_03` tạo `article_03.pdf` 58.980 byte, 2 trang. Trích xuất lại bằng `pdfplumber` cho 5.064 ký tự và giữ được chữ “Nhã nhạc”. File tạm nằm trong `pageindex_pdfs/` (đã được Git ignore); chưa upload lên dịch vụ.
- Streamlit khởi động được trên cổng cục bộ 8512; `GET /_stcore/health` trả `200 ok`. Đây là kiểm tra server khởi động, chưa xác nhận một lượt chat thật.
- **Chưa ghi kết quả chat thực tế** hoặc score hiệu chỉnh ngưỡng vì chưa có index ChromaDB cục bộ và chưa cấu hình LLM/PageIndex API key. Đã thử tải BGE-M3 vào cache cục bộ: file cấu hình tải được, nhưng trọng số không tiến triển sau nhiều lần chờ nên dừng; không đổi sang model khác để tránh hiệu chỉnh sai cấu hình nhóm. Không xem các câu hỏi chuẩn bị ở trên là bằng chứng hệ thống đã trả lời đúng.

## Điều còn hạn chế và bước tiếp theo

- Cần tạo index trên đúng corpus và model embedding đã chốt, chạy hai câu hỏi trên, ghi best dense score, đường retrieval đã chọn, citation và ảnh/chụp log demo. Sau đó chọn `SCORE_THRESHOLD` từ quan sát thực tế và chuyển kết quả cho người phụ trách evaluation.
- Cần kiểm chứng gọi LLM và PageIndex thật sau khi nhóm cung cấp cấu hình hợp lệ; test offline chỉ xác nhận logic nội bộ. Trình tải Chromium của Playwright không hoàn tất trong lần thử tại máy này; bước tạo PDF tạm đã được xác minh bằng Chrome hệ thống.
- Nếu có thêm thời gian, thay đổi đầu tiên là bổ sung kiểm tra thực nghiệm độ ổn định của định dạng citation trên nhiều câu hỏi và đo latency fallback.

## Xác nhận đóng góp

Nội dung trên phản ánh phần code và kiểm thử có thể đối chiếu bằng file/commit. Các mục demo và hiệu chỉnh còn thiếu được nêu rõ, chưa nhận là hoàn tất.

- Ngày: 25/09/2026
- Tên thành viên: Nguyễn Minh Thịnh
