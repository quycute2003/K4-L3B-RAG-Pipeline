# Individual contribution report

---

## Thông tin

- Họ và tên: Vũ Minh Điềm
- Mã học viên: 2A202602858
- Nhóm: DeltaX
- Repository/branch: K4-L3B-RAG-Pipeline / feat/retrieval

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Task 5 — Semantic search | Triển khai dense retrieval bằng embedding chung, query ChromaDB, chuyển cosine distance thành similarity và sắp xếp giảm dần theo score | src/task5_semantic_search.py | Done |
| Task 6 — BM25 lexical search | Xây dựng corpus-based BM25 index, tính score cho query, lọc kết quả score > 0 và trả về SearchResult đúng schema | src/task6_lexical_search.py | Done |
| Task 7 — Reciprocal Rank Fusion | Triển khai RRF theo công thức sum(1/(k+rank)), loại trùng ID, gán retrieval_method="hybrid" và giữ đúng output contract | src/task7_reranking.py | Done |

Chỉ kê khai công việc có thể đối chiếu bằng file, commit, pull request, test hoặc kết quả evaluation.

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Dùng lại chính `embed_texts()` và cấu hình index từ Task 4 cho semantic search.  
   **Lý do/evidence:** Đây là yêu cầu contract của nhóm: Task 4 và Task 5 phải dùng chung embedding model, dimension và `embed_texts()`. Test contract kiểm tra `query_embeddings == [[0.1, 0.2]]` và đầu ra phải `retrieval_method="dense"`.  
   **Trade-off:** Tốn thêm phụ thuộc vào việc Task 4 được xây dựng đúng; nhưng đảm bảo tính nhất quán giữa embedding và index, tránh mismatch khi chạy trên dataset thực.

2. **Quyết định:** RRF chỉ gộp thứ hạng, không cộng trực tiếp cosine score và BM25 score.  
   **Lý do/evidence:** Contract ghi rõ: “RRF dùng công thức sum(1 / (k + rank)), rank bắt đầu từ 1 và chỉ fuse một lần”, và “không so sánh threshold với RRF score”. Test `test_rrf_uses_rank_deduplicates_and_marks_hybrid` xác minh `score == 1/62 + 1/61` và `retrieval_method="hybrid"`.  
   **Trade-off:** Score RRF không trực tiếp có ý nghĩa tuyệt đối như cosine/BM25, nhưng phù hợp để fuse thứ hạng mà không phá vỡ thang đo khác nhau giữa các backend retrieval.

## Kiểm thử và kết quả

- Test hoặc query tôi đã dùng:
  - `pytest tests/test_contracts.py -q -k "semantic_search or lexical_search or rrf"`
- Kết quả trước/sau nếu có:
  - Trước khi implement: có lỗi `NotImplementedError` ở Task 5–7.
  - Sau khi hoàn thiện: `3 passed, 12 deselected in 0.11s`
- Lỗi đã phát hiện và cách xử lý:
  - Thiếu dependency `rank-bm25`; đã cài đặt bằng `python -m pip install rank-bm25` để chạy BM25 đúng môi trường. 
  - BM25 library mặc định trên `rank_bm25` hoạt động đúng với corpus và query có từ khóa rõ ràng; tôi tối ưu hóa việc build index và score calculation để tương thích với cấu trúc project và test contract.

## Điều còn hạn chế

- Một hạn chế cụ thể của phần tôi làm:
  - Dense retrieval phụ thuộc vào ChromaDB và mô hình embedding được cấu hình trong environment; nếu dataset hoặc index cũ không khớp cấu hình, cần rebuild local collection.
- Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện:
  - Tối ưu thêm tuỳ chọn `top_k` và xử lý empty query / stopword một cách rõ ràng hơn trong Task 5–7 để tăng độ robust khi deploy demo thực tế.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 25/09/2026
- Tên thành viên: Vũ Minh Điềm
