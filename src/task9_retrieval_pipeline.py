"""Combine dense and lexical retrieval, then try PageIndex when dense is weak."""

import os

from dotenv import load_dotenv

from .task5_semantic_search import semantic_search
from .task6_lexical_search import lexical_search
from .task7_reranking import rerank_rrf
from .task8_pageindex_vectorless import pageindex_search


load_dotenv()


def _configured_threshold() -> float:
    raw = os.getenv("SCORE_THRESHOLD", "").strip()
    return float(raw) if raw else 0.3


SCORE_THRESHOLD = _configured_threshold()
DEFAULT_TOP_K = 5


def retrieve(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    score_threshold: float = SCORE_THRESHOLD,
    use_reranking: bool = True,
) -> list[dict]:
    """Return PageIndex results when available, otherwise the current ranking."""
    if not query.strip() or top_k <= 0:
        return []

    dense = semantic_search(query, top_k=top_k * 2)
    sparse = lexical_search(query, top_k=top_k * 2) if use_reranking else []
    ranked = (
        rerank_rrf([dense, sparse], top_k=top_k)
        if use_reranking
        else dense[:top_k]
    )

    # Only the original dense similarity has the scale used by this threshold.
    best_dense_score = max((item["score"] for item in dense), default=0.0)
    if best_dense_score < score_threshold:
        try:
            fallback = pageindex_search(query, top_k=top_k)
            if fallback:
                return fallback[:top_k]
        except Exception:
            # An unavailable optional provider must not take down the chat UI.
            pass
    return ranked[:top_k]


if __name__ == "__main__":
    for result in retrieve("Nhã nhạc cung đình Huế", top_k=3):
        print(result)
