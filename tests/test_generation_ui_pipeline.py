"""Offline checks for the modules owned by Generation/UI."""

from pathlib import Path
from types import SimpleNamespace

from src.contracts import validate_generation_result, validate_search_results


def item(number: int, method: str = "hybrid") -> dict:
    return {
        "id": f"chunk-{number}",
        "content": f"Evidence {number}",
        "score": 1.0 - number / 10,
        "metadata": {
            "source": "https://example.org/source",
            "title": f"Source {number}",
            "doc_type": "news",
            "url": "https://example.org/source",
            "chunk_index": number,
        },
        "retrieval_method": method,
    }


def test_generation_citations_follow_sources_after_reordering(monkeypatch):
    import src.task10_generation as generation

    chunks = [item(number) for number in range(4)]
    monkeypatch.setattr(generation, "retrieve", lambda query, top_k: chunks)
    # Reordering is [0, 2, 3, 1], so [2] refers to chunk-2.
    monkeypatch.setattr(generation, "call_llm", lambda system, user: "Thông tin [2].")

    answer = generation.generate_with_citation("Câu hỏi", top_k=4)

    validate_generation_result(answer)
    assert answer["answer"] == "Thông tin [1]."
    assert [source["id"] for source in answer["sources"]] == ["chunk-2"]
    assert answer["retrieval_source"] == "hybrid"


def test_generation_refuses_missing_or_invented_citation(monkeypatch):
    import src.task10_generation as generation

    monkeypatch.setattr(generation, "retrieve", lambda query, top_k: [item(0)])
    monkeypatch.setattr(generation, "call_llm", lambda system, user: "Không có trích dẫn")
    assert generation.generate_with_citation("Câu hỏi")["sources"] == []

    monkeypatch.setattr(generation, "call_llm", lambda system, user: "Nguồn [9]")
    answer = generation.generate_with_citation("Câu hỏi")
    validate_generation_result(answer)
    assert answer["retrieval_source"] == "none"


def test_pageindex_parses_nested_passages_and_preserves_source(monkeypatch):
    import src.task8_pageindex_vectorless as pageindex

    class Client:
        def submit_query(self, doc_id, query):
            return {"retrieval_id": "r-1"}

        def get_retrieval(self, retrieval_id):
            return {
                "status": "completed",
                "retrieved_nodes": [
                    {
                        "node_id": "n-1",
                        "relevant_contents": [[
                            {"page_index": 2, "relevant_content": "Bằng chứng Huế"}
                        ]],
                    }
                ],
            }

    monkeypatch.setattr(
        pageindex,
        "_read_cache",
        lambda: {
            "news/article_01": {
                "doc_id": "d-1",
                "metadata": {
                    "source": "https://example.org/source",
                    "title": "Huế",
                    "doc_type": "news",
                    "url": "https://example.org/source",
                },
            }
        },
    )
    monkeypatch.setattr(pageindex, "_client", lambda: Client())

    output = pageindex.pageindex_search("Huế", top_k=2)

    validate_search_results(output, top_k=2, expected_method="pageindex")
    assert output[0]["content"] == "Bằng chứng Huế"
    assert output[0]["metadata"]["page_index"] == 2
    assert output[0]["metadata"]["source"] == "https://example.org/source"


def test_pageindex_upload_reuses_cached_document_id(monkeypatch):
    import src.task8_pageindex_vectorless as pageindex

    calls = []

    class Client:
        def submit_document(self, path):
            calls.append(path)
            return {"doc_id": "d-1"}

    document = {
        "id": "news/article_01",
        "content": "Public text about Huế",
        "metadata": {
            "source": "https://example.org/source",
            "title": "Huế",
            "doc_type": "news",
            "url": "https://example.org/source",
        },
    }
    cache = {}
    monkeypatch.setattr(pageindex, "_client", lambda: Client())
    monkeypatch.setattr(pageindex, "load_documents", lambda: [document])
    monkeypatch.setattr(pageindex, "_pdf_for", lambda doc: Path("article.pdf"))
    monkeypatch.setattr(pageindex, "_ready", lambda client, doc_id: True)
    monkeypatch.setattr(pageindex, "_read_cache", lambda: cache)
    monkeypatch.setattr(pageindex, "_write_cache", lambda data: cache.update(data))
    monkeypatch.setattr(pageindex, "PDF_DIR", SimpleNamespace(mkdir=lambda **kwargs: None))

    pageindex.upload_documents()
    pageindex.upload_documents()

    assert calls == ["article.pdf"]
    assert cache["news/article_01"]["doc_id"] == "d-1"
