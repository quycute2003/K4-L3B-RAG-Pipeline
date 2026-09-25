# Individual contribution report

## Thông tin

- Họ và tên: Phạm Xuân Quý
- Mã học viên: 2A202602745
- Nhóm: DeltaX
- Repository/branch: K4-L3B-RAG-Pipeline / `main`

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Task 1–3 — Data pipeline | Chọn chủ đề du lịch và văn hóa Huế; thu thập 3 văn bản chính sách và 5 bài viết; lưu nguồn, crawl metadata và chuẩn hóa thành Markdown | `src/task1_collect_legal_docs.py`, `src/task2_crawl_news.py`, `src/task3_convert_markdown.py`, `data/`, commit `fde5ed1` | Done |
| Task 4 — Chunking và indexing | Load front matter, tạo ID ổn định, recursive chunking, embedding BGE-M3 và upsert ChromaDB dùng cosine distance | `src/task4_chunking_indexing.py`, commit `fde5ed1` | Done |
| Tích hợp retrieval | Review và merge Task 5–7 của Vũ Minh Điềm; sửa BM25 để lazy-load cùng corpus chunk từ Task 4; kiểm tra dense/BM25 trên dữ liệu thật | `src/task6_lexical_search.py`, merge commit `3982357` | Done |
| Điều phối nhóm | Lập danh sách thành viên, vai trò và phạm vi công việc; giữ nguồn dữ liệu và cấu hình bí mật ngoài Git | `TEAMMATES.md`, `.gitignore` | Done |

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Chọn corpus hẹp về du lịch và văn hóa tại Quần thể Di tích Cố đô Huế, đồng thời giữ URL và metadata xuyên suốt pipeline.
   **Lý do/evidence:** Corpus gồm 3 văn bản chính sách và 5 trang công khai, đáp ứng số lượng tối thiểu và cho phép đối chiếu từ Markdown về nguồn gốc.
   **Trade-off:** Phạm vi hẹp giúp citation đáng tin cậy nhưng chatbot chưa bao phủ toàn bộ du lịch Thừa Thiên Huế.

2. **Quyết định:** Dùng recursive chunking `500/50`, ID theo document và `chunk_index`, embedding chuẩn hóa `BAAI/bge-m3` rồi upsert vào ChromaDB cosine.
   **Lý do/evidence:** Cấu hình tạo 939 chunk từ 8 tài liệu, embedding 1.024 chiều; index lại vẫn giữ 939 bản ghi và không nhân bản dữ liệu.
   **Trade-off:** BGE-M3 hỗ trợ tiếng Việt tốt nhưng tải model lớn và chạy chậm hơn trên CPU.

## Kiểm thử và kết quả

- Data và Task 4: 5 test mục tiêu pass; corpus có đủ 3 legal, 5 news và hai nhánh Markdown chuẩn hóa.
- Contract Task 4: ID chunk duy nhất, metadata nguồn và `chunk_index` được giữ; kích thước chunk đúng giới hạn.
- Chạy thật: 8 document → 939 chunk; embedding dimension 1.024; re-index `939 → 939`.
- Kiểm tra tích hợp: 3 contract test Task 5–7 pass; dense và BM25 đều trả ba kết quả hợp lệ cho truy vấn về Ngọ Môn.
- Lỗi đã xử lý: loại chunk chỉ chứa dấu câu, ngăn cấu hình ChromaDB lệch model và sửa Task 6 không load corpus khi chạy thật.

## Điều còn hạn chế

- Một số văn bản PDF có thể còn nhiễu bố cục sau khi chuyển đổi; embedding BGE-M3 trên CPU có thời gian khởi tạo tương đối dài.
- Nếu có thêm thời gian, tôi sẽ làm sạch cấu trúc văn bản pháp lý sâu hơn và đánh giá nhiều cấu hình chunk trước khi chốt pipeline.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 25/09/2026
- Tên thành viên: Phạm Xuân Quý
