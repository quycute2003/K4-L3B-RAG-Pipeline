"""Run a reproducible retrieval-only A/B evaluation.

Config A uses dense search. Config B uses the same dense candidates plus BM25
and one RRF fusion.  The script intentionally measures only retrieval-stage
proxies: a matching source document in the returned chunks is a context-recall
hit, and the fraction of returned chunks from that document is context
precision.  Faithfulness and answer relevance require Task 10 output and are
therefore not inferred here.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from statistics import mean


ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = Path(__file__).with_name("golden_dataset.json")

# Evaluation reuses the already-downloaded BGE-M3 model.  This avoids a
# network HEAD request for every benchmark run and makes results reproducible.
os.environ.setdefault("HF_HUB_OFFLINE", "1")

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.task5_semantic_search import semantic_search
from src.task6_lexical_search import lexical_search
from src.task7_reranking import rerank_rrf


def load_cases(path: Path) -> list[dict]:
    cases = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(cases, list) or not cases:
        raise ValueError("Golden dataset must be a non-empty JSON array")
    required = {"id", "question", "expected_context", "source_document"}
    for index, case in enumerate(cases):
        missing = required - case.keys()
        if missing:
            raise ValueError(f"Case {index} is missing: {', '.join(sorted(missing))}")
    return cases


def dense_only(query: str, top_k: int) -> list[dict]:
    return semantic_search(query, top_k=top_k)


def hybrid_rrf(query: str, top_k: int) -> list[dict]:
    candidate_k = top_k * 2
    return rerank_rrf(
        [
            semantic_search(query, top_k=candidate_k),
            lexical_search(query, top_k=candidate_k),
        ],
        top_k=top_k,
        k=60,
    )


def source_matches(result: dict, expected_document: str) -> bool:
    """A chunk ID begins with its stable standardized document ID."""
    return str(result.get("id", "")).startswith(f"{expected_document}::")


def run_config(name: str, search, cases: list[dict], top_k: int) -> dict:
    per_case = []
    for case in cases:
        started = time.perf_counter()
        results = search(case["question"], top_k)
        latency_ms = (time.perf_counter() - started) * 1000
        hits = sum(source_matches(item, case["source_document"]) for item in results)
        per_case.append(
            {
                "id": case["id"],
                "question": case["question"],
                "expected_document": case["source_document"],
                "returned_ids": [item["id"] for item in results],
                "context_recall_proxy": float(hits > 0),
                "context_precision_proxy": round(hits / len(results), 4) if results else 0.0,
                "latency_ms": round(latency_ms, 2),
            }
        )

    return {
        "name": name,
        "top_k": top_k,
        "metrics": {
            "context_recall_proxy": round(mean(row["context_recall_proxy"] for row in per_case), 4),
            "context_precision_proxy": round(mean(row["context_precision_proxy"] for row in per_case), 4),
            "mean_latency_ms": round(mean(row["latency_ms"] for row in per_case), 2),
        },
        "per_case": per_case,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate dense-only against hybrid + RRF")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("retrieval_ab_results.json"),
    )
    args = parser.parse_args()
    if args.top_k <= 0:
        raise ValueError("--top-k must be positive")

    cases = load_cases(DATASET_PATH)
    # Model loading dominates the first dense call, so exclude startup time from
    # the latency comparison.  Both retrieval paths are warmed before timing.
    warmup_query = cases[0]["question"]
    dense_only(warmup_query, args.top_k)
    hybrid_rrf(warmup_query, args.top_k)
    config_a = run_config("dense-only", dense_only, cases, args.top_k)
    config_b = run_config("hybrid-rrf", hybrid_rrf, cases, args.top_k)
    payload = {
        "dataset": str(DATASET_PATH.relative_to(ROOT)).replace("\\", "/"),
        "case_count": len(cases),
        "retrieval_only": True,
        "note": "Faithfulness and answer relevance are not measured until Task 10 is available.",
        "config_a": config_a,
        "config_b": config_b,
        "delta_b_minus_a": {
            key: round(config_b["metrics"][key] - config_a["metrics"][key], 4)
            for key in ("context_recall_proxy", "context_precision_proxy", "mean_latency_ms")
        },
    }
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.output} for {len(cases)} cases.")
    for label, config in (("A", config_a), ("B", config_b)):
        metrics = config["metrics"]
        print(
            f"Config {label}: recall={metrics['context_recall_proxy']:.4f}, "
            f"precision={metrics['context_precision_proxy']:.4f}, "
            f"mean latency={metrics['mean_latency_ms']:.2f} ms"
        )


if __name__ == "__main__":
    main()
