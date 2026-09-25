# RAG evaluation results

> Trạng thái ngày 25/09/2026: đã chạy A/B end-to-end trên 16 golden case. Config A (dense-only) cao hơn Config B (hybrid + RRF) ở faithfulness, answer relevance và context precision; hai config cùng context recall 1.000.

## Run information

| Field | Value |
|---|---|
| Evaluation date | 25/09/2026 — A/B end-to-end hoàn tất |
| Framework and version | Ragas 0.4.3 |
| Evaluator model | `gpt-4o-mini`; embedding evaluator `text-embedding-3-small` |
| Generator model | `gpt-4o-mini` qua OpenAI |
| Embedding model | `sentence_transformers` / `BAAI/bge-m3`, 1.024 chiều |
| Corpus version/commit | `8fc2258`; 3 legal + 5 news; 939 chunk |
| Golden dataset size | 16; 6 keyword, 5 semantic, 5 case dễ nhầm nguồn; phủ 5 news + 2 kế hoạch du lịch |
| `top_k` | 5, cố định cho Config A và Config B |
| Fallback threshold and calibration | `0.3`; chưa calibration riêng vì baseline A/B chỉ so dense và hybrid + RRF |

## Configurations

- **Config A — dense-only:** `semantic_search`, cosine similarity, `top_k=5`.
- **Config B — hybrid + RRF:** dense + BM25, fuse đúng một lần bằng RRF với `k=60`, `top_k=5`.

Hai cấu hình dùng cùng golden dataset, `top_k=5`, Task 10 system prompt, generator và evaluator; chỉ retrieval strategy khác nhau. Chạy end-to-end bằng `py group_project/evaluation/run_end_to_end_ab.py`.

## Overall scores

| Metric | Config A | Config B | Delta B−A |
|---|---:|---:|---:|
| Faithfulness | 0.9792 | 0.9375 | -0.0417 |
| Answer relevance | 0.6581 | 0.6161 | -0.0420 |
| Context recall | 1.0000 | 1.0000 | +0.0000 |
| Context precision | 0.9186 | 0.9142 | -0.0044 |
| **Average** | **0.8890** | **0.8670** | **-0.0220** |

Các số trên lấy từ `end_to_end_ab_results.json`; mỗi config có 16 câu trả lời và được RAGAS chấm bằng cùng evaluator. `retrieval_ab_results.json` là phép đo bổ sung theo document ID: cả hai config có recall proxy 1.000 và precision proxy 0.725. Latency đã warm-up: Config A 61.30 ms, Config B 118.77 ms; B chậm hơn 57.47 ms do BM25 và RRF.

## A/B comparison

- Cấu hình tốt hơn: **Config A — dense-only**. Nó cao hơn B 0.0417 faithfulness, 0.0420 answer relevance và 0.0044 context precision; context recall hòa 1.000.
- Evidence: `end_to_end_ab_results.json` và `retrieval_ab_results.json` lưu score/answer/context theo từng case. Hybrid không tăng recall hoặc precision proxy, đồng thời chèn thêm chunk Kế hoạch 188 ở các câu hỏi về Kế hoạch 275.
- Trade-off: Config B chậm hơn 57.47 ms ở retrieval và có average RAGAS thấp hơn 0.0220. Cost generation/evaluator giữ nguyên về số case và model; B không có lợi ích metric bù lại chi phí này.

## Worst performers

| # | Question | Config | Faithfulness | Relevance | Recall | Precision | Failure stage | Root cause |
|---:|---|---|---:|---:|---:|---:|---|---|
| 1 | Đến năm 2030, Kế hoạch 275 định hướng vị thế du lịch Huế như thế nào? | B | 0.0000 | 0.0000 | 1.0000 | 1.0000 | generation | Generator trả safe refusal dù context có chunk Kế hoạch 275; các chunk Kế hoạch 188 được RRF xếp lẫn trong context làm evidence mục tiêu 2030 không đủ nổi bật. |
| 2 | Kế hoạch 275 khuyến khích người dân địa phương tham gia du lịch bằng những hoạt động nào? | B | 1.0000 | 0.6171 | 1.0000 | 0.2000 | retrieval | RRF lấy 3/5 chunk đầu từ Kế hoạch 188 vì trùng cụm “du lịch cộng đồng”; câu trả lời còn thêm chi tiết không cần thiết về lễ hội/sự kiện. |
| 3 | Kiểu trang trí nào kết hợp một ô thơ hoặc đại tự với một bức họa trong kiến trúc cung đình Huế? | A | 0.6667 | 0.6248 | 1.0000 | 1.0000 | generation/evaluation | Tất cả context đúng tài liệu, nhưng câu trả lời diễn giải thêm việc nó trở thành phong cách thời Nguyễn; cần ràng buộc câu trả lời chỉ nêu đúng mệnh đề được hỏi và dùng reference context đầy đủ hơn. |

## Recommendations

| Priority | Action | Evidence from failure analysis | Expected impact | How to verify |
|---:|---|---|---|---|
| 1 | Giữ dense-only làm baseline nộp bài; chỉ dùng hybrid sau khi cải thiện xử lý mã kế hoạch | A thắng B ở average RAGAS (+0.0220) và nhanh hơn 57.47 ms | Tránh thêm độ trễ mà không tăng chất lượng | Chạy lại hai config sau thay đổi; chỉ đổi baseline nếu B tăng ít nhất một metric quan trọng mà không làm giảm recall |
| 2 | Rerank/filter theo metadata khi query chứa mã kế hoạch như `275/KH-UBND` | Case B `plan-275-02` safe-refusal; `plan-275-03` precision 0.2000 do lẫn Kế hoạch 188 | Giảm nhiễu Kế hoạch 188, tăng độ nổi bật evidence của Kế hoạch 275 | Chạy lại hai case này; không còn safe refusal và context precision của `plan-275-03` tăng trên 0.20 |
| 3 | Siết prompt thành trả lời đúng phạm vi câu hỏi và mở rộng reference context cho case có một mệnh đề | `poetry-01` có context precision/recall 1.0 nhưng faithfulness 0.6667 do câu trả lời diễn giải rộng hơn yêu cầu | Tăng faithfulness mà không thay retrieval | Chạy lại `poetry-01`; giữ context không đổi, faithfulness phải vượt 0.6667 |

## Bonus experiments

Chưa thực hiện bonus experiment. Chỉ bổ sung HyDE, reranker hoặc memory sau khi baseline A/B có số liệu hoàn chỉnh.

| Experiment | Baseline | Metric delta | Latency/cost delta | Conclusion |
|---|---|---:|---:|---|
| Chưa chạy | Dense-only và hybrid + RRF | — | — | Ưu tiên hoàn thiện baseline trước |
