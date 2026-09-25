# Individual contribution report

## Thông tin

- Họ và tên: Vũ Minh Điềm
- Mã học viên: 2A202602858
- Nhóm: DeltaX
- Repository/branch: K4-L3B-RAG-Pipeline / `diemvu12369`

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Task 5 — Semantic search | Triển khai dense retrieval bằng embedding chung, query ChromaDB, chuyển cosine distance thành similarity và sắp xếp giảm dần theo score | `src/task5_semantic_search.py`, `b1db933` | Done |
| Task 6 — BM25 lexical search | Xây dựng BM25 index trên corpus chunk, tính score cho query, lọc kết quả có score dương và trả về `SearchResult` đúng schema | `src/task6_lexical_search.py`, `b1db933` | Done |
| Task 7 — Reciprocal Rank Fusion | Triển khai RRF theo công thức `sum(1/(k+rank))`, loại trùng ID, gán `retrieval_method="hybrid"` và giữ đúng output contract | `src/task7_reranking.py`, `b1db933` | Done |

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Dùng lại chính `embed_texts()` và cấu hình index từ Task 4 cho semantic search.
   **Lý do/evidence:** Contract yêu cầu Task 4 và Task 5 dùng chung embedding model, dimension và hàm embedding. Contract test xác minh query embedding và output `retrieval_method="dense"`.
   **Trade-off:** Task 5 phụ thuộc vào index của Task 4, nhưng tránh mismatch model hoặc dimension giữa corpus và query.

2. **Quyết định:** RRF chỉ gộp thứ hạng, không cộng trực tiếp cosine score và BM25 score.
   **Lý do/evidence:** Hai hệ thống dùng thang điểm khác nhau; RRF theo contract dùng `sum(1/(k+rank))`, với rank bắt đầu từ 1.
   **Trade-off:** RRF score không có ý nghĩa tuyệt đối như cosine hoặc BM25, nhưng phù hợp để hợp nhất các bảng xếp hạng khác thang đo.

## Kiểm thử và kết quả

- Test đã dùng: `pytest tests/test_contracts.py -q -k "semantic_search or lexical_search or rrf"`.
- Trước khi triển khai: Task 5–7 trả `NotImplementedError`.
- Sau khi triển khai: các contract test của semantic search, lexical search và RRF đều pass.
- BM25 được triển khai trực tiếp trong module để giữ cách tokenize và tính điểm rõ ràng, không phụ thuộc dịch vụ bên ngoài.

## Điều còn hạn chế

- Dense retrieval phụ thuộc vào ChromaDB và model embedding được cấu hình trong môi trường; cần rebuild index nếu cấu hình hoặc corpus thay đổi.
- Nếu có thêm thời gian, tôi sẽ bổ sung xử lý stopword tiếng Việt và cache BM25 index để tránh build lại ở mỗi truy vấn.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 25/09/2026
- Tên thành viên: Vũ Minh Điềm
