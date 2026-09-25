# Thành viên nhóm DeltaX

**Chủ đề:** Chatbot RAG hỗ trợ tra cứu thông tin du lịch và văn hóa tại Quần thể Di tích Cố đô Huế.

| STT | Họ và tên | Mã học viên | Vai trò | Nhánh | Phần việc phụ trách |
| ---: | --- | --- | --- | --- | --- |
| 1 | Phạm Xuân Quý | 2A202602745 | Data & Indexing | `feat/data-pipeline` | Chọn chủ đề, thu thập và chuẩn hóa dữ liệu; chunking, embedding và ChromaDB (`task1`–`task4`) |
| 2 | Vũ Minh Điềm | 2A202602858 | Retrieval | `feat/retrieval` | Dense search, BM25 và RRF (`task5`–`task7`) |
| 3 | Nguyễn Minh Thịnh | 2A202602556 | Generation/UI | `feat/generation-ui` | PageIndex, fallback, retrieval pipeline, generation có citation và giao diện Streamlit (`task8`–`task10`, `app.py`) |
| 4 | Nguyễn Hoàng Tuyên | 2A202602439 | Evaluation/Integration | `feat/evaluation-integration` | Golden dataset, 4 metrics, A/B comparison, kiểm thử, tích hợp và báo cáo kết quả |

## Quy ước phối hợp

- Mỗi thành viên commit trên nhánh phần việc của mình và ghi lại các commit để hoàn thiện báo cáo cá nhân.
- Các module tuân thủ schema và interface trong `docs/MODULE_CONTRACTS.md`.
- Nguyễn Hoàng Tuyên phụ trách kiểm tra tích hợp sau mỗi lần merge; cả nhóm cùng chịu trách nhiệm cho demo và chất lượng bài nộp cuối.
- Không commit `.env`, API key hoặc thông tin bí mật lên repository.
