# Individual contribution report

## Thông tin

- Họ và tên: Nguyễn Hoàng Tuyên
- Mã học viên: 2A202602439
- Nhóm: DeltaX
- Repository/branch: K4-L3B-RAG-Pipeline / `main`

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Golden dataset | Xây dựng 16 câu hỏi grounded từ 5 nguồn news và 2 kế hoạch du lịch; mỗi case có `question`, `expected_answer`, `expected_context`, ID, category và tài liệu nguồn | `group_project/evaluation/golden_dataset.json` | Done |
| A/B retrieval evaluation | Viết harness so sánh dense-only với hybrid + RRF, cố định `top_k=5`, warm-up embedding trước khi đo và lưu returned IDs, recall/precision proxy, latency theo từng case | `group_project/evaluation/run_retrieval_ab.py`, `retrieval_ab_results.json` | Done |
| End-to-end RAGAS evaluation | Viết runner tạo câu trả lời cho hai cấu hình bằng cùng prompt/generator, chấm faithfulness, answer relevance, context recall, context precision và lưu metric theo case | `group_project/evaluation/run_end_to_end_ab.py`, `end_to_end_ab_results.json` | Done |
| Phân tích lỗi và báo cáo | Tổng hợp overall score, delta B−A, latency, ba worst case, root cause và recommendation có tiêu chí chạy lại | `group_project/evaluation/RESULT.md`, `reports/RESULT.md` | Done |
| Kiểm thử/tích hợp sau merge | Pull merge Task 8–10, chạy test generation/UI và acceptance; kiểm tra cấu hình model/key không lộ secret; xử lý timeout Hugging Face bằng cache offline cho benchmark | `tests/test_generation_ui_pipeline.py`, `tests/test_acceptance.py` | Done |

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** So sánh Config A dense-only với Config B hybrid + RRF trong cùng một golden dataset, `top_k=5`, system prompt, generator và RAGAS evaluator.
   **Lý do/evidence:** Chỉ thay retrieval strategy mới quy được chênh lệch cho hybrid/RRF. Trên 16 case, dense-only đạt average RAGAS 0.8890, cao hơn hybrid 0.8670; context recall cùng là 1.0000.
   **Trade-off:** Thiết kế này không đo PageIndex/fallback trong baseline A/B, nhưng cho kết luận rõ ràng về lợi ích thực của RRF.

2. **Quyết định:** Dùng cache cục bộ BGE-M3 ở chế độ offline riêng cho các runner evaluation.
   **Lý do/evidence:** Hugging Face metadata check từng timeout trước khi benchmark; model `BAAI/bge-m3` đã được tải khi indexing. Offline chỉ chặn metadata request, không đổi model, corpus, chunking hoặc gọi OpenAI/RAGAS.
   **Trade-off:** Máy chạy evaluation phải có cache model đầy đủ; nếu không có, runner báo lỗi thay vì tự tải model.

## Kiểm thử và kết quả

- `py -m pytest tests\test_generation_ui_pipeline.py tests\test_acceptance.py -q`: **9 passed**.
- `py -m pytest tests\test_acceptance.py -q`: **5 passed** sau khi hoàn tất report/dataset.
- A/B retrieval warm-run: dense-only và hybrid cùng recall proxy 1.000, precision proxy 0.725; hybrid chậm hơn 57.47 ms (118.77 ms so với 61.30 ms).
- A/B end-to-end trên 16 case với `gpt-4o-mini`: dense-only đạt faithfulness 0.9792, answer relevance 0.6581, context recall 1.0000, context precision 0.9186; hybrid tương ứng 0.9375, 0.6161, 1.0000, 0.9142.
- Lỗi đã phát hiện: hybrid lẫn chunk Kế hoạch 188 vào câu hỏi Kế hoạch 275; một case trả safe refusal dù evidence đúng có trong context. Báo cáo đã ghi root cause và cách kiểm chứng reranking/filter theo metadata.

## Điều còn hạn chế

- Golden dataset có 16 case, đủ acceptance nhưng còn nhỏ; kết quả RAGAS có thể biến động theo LLM evaluator. RAGAS cũng cảnh báo một số lượt chỉ nhận được 1 generation thay vì 3.
- Nếu có thêm thời gian, tôi sẽ thêm metadata-aware reranking cho các truy vấn chứa số/mã kế hoạch như `275/KH-UBND`, mở rộng golden set và chạy lại A/B để kiểm tra rằng hybrid chỉ được chọn khi cải thiện metric quan trọng mà không làm giảm recall.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 25/09/2026
- Tên thành viên: Nguyễn Hoàng Tuyên
