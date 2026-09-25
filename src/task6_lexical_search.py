"""
Task 6 — Lexical search bằng BM25.

Dùng cùng corpus chunks với Task 5. BM25 phù hợp với từ khóa chính xác, mã tài
liệu và tên riêng. Output phải theo SearchResult và sort score giảm dần.
"""

import math
import re
from collections import Counter

from .task4_chunking_indexing import chunk_documents, load_documents


CORPUS: list[dict] = []


class BM25Index:
    """BM25 scorer with stable positive relevance for short keyword queries."""

    def __init__(self, corpus: list[list[str]], *, k1: float = 1.5, b: float = 0.75):
        self.corpus = corpus
        self.k1 = k1
        self.b = b
        self.doc_lengths = [len(doc) for doc in corpus]
        self.avgdl = sum(self.doc_lengths) / len(corpus) if corpus else 0.0
        self.doc_freqs = {}
        for doc in corpus:
            counts = Counter(doc)
            for term, freq in counts.items():
                self.doc_freqs[term] = self.doc_freqs.get(term, 0) + 1

    def _idf(self, term: str) -> float:
        doc_freq = self.doc_freqs.get(term, 0)
        if doc_freq == 0 or not self.corpus:
            return 0.0
        base = math.log(((len(self.corpus) - doc_freq + 0.5) / (doc_freq + 0.5)))
        return max(base + 1.0, 1e-6)

    def get_scores(self, query_tokens: list[str]) -> list[float]:
        if not self.corpus:
            return []
        if not query_tokens:
            return [0.0 for _ in self.corpus]

        scores = [0.0 for _ in self.corpus]
        for term in set(query_tokens):
            idf = self._idf(term)
            if idf <= 0:
                continue
            for idx, doc_tokens in enumerate(self.corpus):
                term_count = doc_tokens.count(term)
                if term_count == 0:
                    continue
                denominator = term_count + self.k1 * (
                    1 - self.b + self.b * self.doc_lengths[idx] / max(self.avgdl, 1e-9)
                )
                scores[idx] += idf * (
                    term_count * (self.k1 + 1) / max(denominator, 1e-9)
                )
        return scores


def build_bm25_index(corpus: list[dict]):
    """Tạo BM25 index từ cùng corpus chunks của Task 4."""
    tokenized = [re.findall(r"\w+", str(item["content"]).lower()) for item in corpus]
    return BM25Index(tokenized)


def _get_corpus() -> list[dict]:
    """Lazy-load đúng corpus chunks đã dùng để tạo dense index ở Task 4."""
    global CORPUS
    if not CORPUS:
        CORPUS = chunk_documents(load_documents())
    return CORPUS


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """Trả về BM25 SearchResult theo score giảm dần."""
    if top_k <= 0:
        return []
    if not isinstance(query, str) or not query.strip():
        return []

    corpus = _get_corpus()
    bm25 = build_bm25_index(corpus)
    query_tokens = re.findall(r"\w+", query.lower())
    if not query_tokens:
        return []

    scores = bm25.get_scores(query_tokens)
    ranked_indices = sorted(range(len(scores)), key=lambda idx: scores[idx], reverse=True)

    results = []
    for index in ranked_indices[:top_k]:
        score = float(scores[index])
        if score <= 0:
            continue
        item = corpus[index]
        results.append(
            {
                "id": item["id"],
                "content": item["content"],
                "score": score,
                "metadata": item["metadata"],
                "retrieval_method": "bm25",
            }
        )
    return results


if __name__ == "__main__":
    for result in lexical_search("test query", top_k=3):
        print(result)
