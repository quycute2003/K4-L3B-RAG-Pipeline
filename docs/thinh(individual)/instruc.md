# Checklist Lab 08 — RAG Pipeline (nhóm DeltaX)

Tài liệu này tổng hợp việc cần làm của **cả nhóm** và phần việc của **Nguyễn Minh Thịnh** (mã học viên `2A202602556`, nhánh `feat/generation-ui`) theo [TEAMMATES.md](../../TEAMMATES.md). Chủ đề đã chọn: chatbot tra cứu du lịch và văn hóa tại Quần thể Di tích Cố đô Huế. Xem [hợp đồng module](../MODULE_CONTRACTS.md) trước khi sửa hàm hoặc nối các module.

> Đây là checklist thực hiện, không phải xác nhận các mục đã hoàn thành. Trạng thái cần được kiểm tra lại trên commit dùng để nộp.

## 1. Chuẩn bị repository và phối hợp nhóm

- [ ] Làm việc trên repository đúng lớp `K4-L3B-RAG-Pipeline`, từ `main` tạo nhánh theo [TEAMMATES.md](../../TEAMMATES.md): Data & Indexing `feat/data-pipeline` (Quý), Retrieval `feat/retrieval` (Điềm), Generation/UI `feat/generation-ui` (Thịnh), Evaluation/Integration `feat/evaluation-integration` (Tuyên).
- [ ] Dùng Python 3.10–3.13 theo [pyproject.toml](../../pyproject.toml), cài dependency và Chromium. Trên PowerShell:

  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  python -m pip install --upgrade pip setuptools wheel
  python -m pip install -e ".[dev]"
  python -m playwright install chromium
  Copy-Item .env.example .env
  ```

- [ ] Điền provider/model/key cần dùng vào `.env` cục bộ; giữ `.env`, API key, cache và vector DB khỏi commit. `.env.example` chỉ liệt kê tên biến. Ghi lại commit, file, test và kết quả mình phụ trách để làm báo cáo cá nhân.

## 2. Corpus và chuẩn hóa — Quý phụ trách, cả nhóm kiểm tra nguồn

- [ ] Chốt danh sách nguồn ở [data/SOURCES.md](../../data/SOURCES.md); bảo đảm ít nhất **3** tài liệu chính sách PDF/DOC/DOCX trong `data/landing/legal/` và **5** bài viết công khai trong `data/landing/news/`. Mỗi JSON bài viết có `url`, `title`, `date_crawled`, `content_markdown`.
- [ ] Hoàn thiện/chạy `src/task1_collect_legal_docs.py`, `src/task2_crawl_news.py`, `src/task3_convert_markdown.py`; đầu ra tương ứng nằm ở `data/standardized/legal/` và `data/standardized/news/`. Chạy lại không tạo bản sao; mỗi Markdown truy ngược được file landing và URL nguồn.
- [ ] Đối chiếu thủ công một số đoạn Markdown với nguồn gốc; kiểm tra độ dài, metadata, quyền sử dụng và tránh dữ liệu cá nhân. Sau khi chốt corpus, thay đổi nội dung phải kéo theo chạy lại index và evaluation.

  ```powershell
  python -m src.task1_collect_legal_docs
  python -m src.task2_crawl_news
  python -m src.task3_convert_markdown
  pytest tests/test_acceptance.py -q
  ```

## 3. Index và tìm kiếm — Quý, Điềm phụ trách

- [ ] Task 4 (`src/task4_chunking_indexing.py`): load tài liệu, chunk giữ `source`/`title`/`doc_type`/`url` và `chunk_index`, embed bằng `embed_texts()`, upsert ChromaDB với ID ổn định. Ghi cấu hình chunk thực tế (`CHUNK_SIZE`, `CHUNK_OVERLAP`, phương pháp) và model embedding dùng khi đánh giá; kiểm tra chạy index lần hai không nhân bản chunk.
- [ ] Task 5 (`src/task5_semantic_search.py`): query dùng **chính `embed_texts()` của Task 4**; cosine distance chuyển sang similarity, trả `retrieval_method="dense"`.
- [ ] Task 6 (`src/task6_lexical_search.py`): BM25 trên cùng corpus chunk, trả `retrieval_method="bm25"`.
- [ ] Task 7 (`src/task7_reranking.py`): RRF theo ID, `sum(1 / (k + rank))` với rank từ 1; copy item trước khi thay score/method thành `hybrid`, không sửa các ranked list đầu vào. Mỗi đường trả tối đa `top_k`, không trùng ID, score giảm dần.

  ```powershell
  python -m src.task4_chunking_indexing
  python -m src.task5_semantic_search
  python -m src.task6_lexical_search
  python -m src.task7_reranking
  pytest tests/test_contracts.py -q
  ```

## 4. Phần Thịnh — fallback, generation và UI

**Đầu vào cần thống nhất với Điềm:** `semantic_search()` và `lexical_search()` trả `SearchResult` đúng [schema](../MODULE_CONTRACTS.md), có ID và metadata nguồn còn nguyên; `rerank_rrf()` chỉ fuse một lần. **Đầu ra cần bàn giao cho Tuyên:** truy xuất dense-only và hybrid có thể chạy trên cùng câu hỏi, cùng `top_k`, cùng generator để đánh giá A/B.

- [ ] **Task 8 — `src/task8_pageindex_vectorless.py`:** nếu dùng PageIndex, đọc `PAGEINDEX_API_KEY` từ `.env`, upload tài liệu tương thích, cache mapping source → document ID, đặt timeout, parse node về `SearchResult` với `retrieval_method="pageindex"`. Không để lỗi dịch vụ làm giao diện crash. Nếu nhóm chọn cơ chế fallback khác, thống nhất cách đáp ứng yêu cầu fallback và ghi rõ trong báo cáo.
- [ ] **Task 9 — `src/task9_retrieval_pipeline.py`:** `retrieve()` gọi dense và BM25, fuse RRF **đúng một lần**, lấy **best cosine score gốc của dense** để so `score_threshold`. Dưới threshold thì thử fallback; nếu fallback lỗi hoặc không có kết quả, giữ hybrid hiện có để generation quyết định có đủ bằng chứng hay không. Hiệu chỉnh threshold bằng ít nhất một query đúng chủ đề và một query ngoài chủ đề; ghi query, score, threshold và hành vi vào báo cáo. Không so ngưỡng với RRF score.
- [ ] **Task 10 — `src/task10_generation.py`:** `reorder_for_llm()` giữ đủ ID và không mutate input; `format_context()` ghi rõ title/source cho từng chunk; `call_llm()` dùng `LLM_PROVIDER`/`LLM_MODEL` của provider nhóm chọn và trả text thuần. `generate_with_citation()` trả đúng `answer`, `sources`, `retrieval_source`; nguồn hiển thị phải là các `SearchResult` thực sự đưa vào context. Khi không đủ bằng chứng hoặc không có chunk, trả lời từ chối xác minh an toàn với `sources=[]`, `retrieval_source="none"`.
- [ ] **`app.py`:** nhận query và `top_k`, gọi `generate_with_citation(query, top_k)`, hiển thị answer, title/URL hoặc source, retrieval method và score từ `sources`. Lưu cả answer, sources và retrieval source trong `st.session_state` để lịch sử chat render lại đúng citation. Demo một câu đúng domain có nguồn mở và đối chiếu được; một câu ngoài domain không crash và không bịa.

  ```powershell
  pytest tests/test_contracts.py -q
  streamlit run app.py
  ```

## 5. Evaluation — Tuyên phụ trách, Thịnh hỗ trợ chạy hai cấu hình

- [ ] Tạo ít nhất **15** case bám corpus trong `group_project/evaluation/golden_dataset.json`, mỗi case có `question`, `expected_answer`, `expected_context`. Có câu dễ tìm theo từ khóa, câu cần tương đồng ngữ nghĩa và câu dễ nhầm nguồn.
- [ ] Chạy **Config A: dense-only** và **Config B: hybrid + RRF** trên cùng golden dataset; giữ nguyên generator, evaluator, prompt và `top_k`. Ghi ngày chạy, corpus commit, model, chunking, threshold và query hiệu chỉnh.
- [ ] Điền [group_project/evaluation/RESULT.md](../../group_project/evaluation/RESULT.md): faithfulness, answer relevance, context recall, context precision, delta B−A, latency/cost nếu đo được; đọc ba case kém nhất, phân loại lỗi data/retrieval/generation, nêu root cause và recommendation có cách kiểm tra lại. Không để `TODO` trong báo cáo cuối.
- [ ] Bonus (nếu có) cần baseline, metric delta và thay đổi latency/cost; tính năng chạy riêng chưa đủ làm bằng chứng cải thiện.

## 6. Kiểm tra, báo cáo cá nhân và nộp

- [ ] Mỗi thành viên copy [template cá nhân](../../group_project/ịndividual/INDIVIDUAL_REPORT.md) vào `reports/` theo tên `K4-L3B-MSSV-Name.md`; ghi việc trực tiếp làm bằng file/commit/PR/test/kết quả đánh giá. Thịnh ghi rõ Task 8–10, `app.py`, quyết định threshold/citation/fallback và demo thực tế.
- [ ] Chạy đủ ba checkpoint trên commit nộp; test pass không thay việc kiểm tra nội dung nguồn và citation thủ công.

  ```powershell
  pytest tests/test_contracts.py -q
  pytest tests/test_acceptance.py -q
  pytest -q
  ```

- [ ] Kiểm tra `git status`, file bí mật/cache, cấu trúc root, README tái lập được, demo query đúng/ngoài domain và bảng A/B. Sau khi tích hợp, cả nhóm dùng chung một URL repository để nộp lên VLearn.

## Trạng thái khi lập checklist

Corpus Huế và [TEAMMATES.md](../../TEAMMATES.md) đã có trong repo. Tại thời điểm đọc, Task 8–10 và `app.py` vẫn chứa placeholder/`NotImplementedError`; `group_project/evaluation/golden_dataset.json` đang rỗng và `RESULT.md` còn `TODO`. Các mục đó cần được triển khai và kiểm chứng trước khi coi project hoàn tất.
