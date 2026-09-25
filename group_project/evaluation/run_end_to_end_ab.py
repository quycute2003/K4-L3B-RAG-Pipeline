"""Evaluate dense-only and hybrid+RRF with an identical RAGAS setup.

The only experimental variable is retrieval. Both configurations use the same
golden cases, Task 10 system prompt/generator, evaluator models, and top_k.
The script writes results only after both configurations complete successfully.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from statistics import mean

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = Path(__file__).with_name("golden_dataset.json")
DEFAULT_OUTPUT = Path(__file__).with_name("end_to_end_ab_results.json")

# The local BGE-M3 cache has already been populated by the indexing pipeline.
# Do not let model metadata checks make this reproducible benchmark depend on
# a live Hugging Face connection.
os.environ.setdefault("HF_HUB_OFFLINE", "1")

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.task5_semantic_search import semantic_search
from src.task6_lexical_search import lexical_search
from src.task7_reranking import rerank_rrf
from src.task10_generation import SAFE_REFUSAL, SYSTEM_PROMPT, call_llm, format_context, reorder_for_llm


def require_openai_configuration() -> tuple[str, str]:
    load_dotenv(ROOT / ".env")
    provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()
    model = os.getenv("LLM_MODEL", "").strip()
    if provider != "openai":
        raise ValueError("RAGAS runner currently requires LLM_PROVIDER=openai")
    if not model or not os.getenv("OPENAI_API_KEY", "").strip():
        raise ValueError("Set LLM_MODEL and OPENAI_API_KEY in .env")
    return model, os.getenv("EVALUATOR_EMBEDDING_MODEL", "text-embedding-3-small").strip()


def load_cases() -> list[dict]:
    cases = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    required = {"id", "question", "expected_answer", "expected_context"}
    for case in cases:
        missing = required - case.keys()
        if missing:
            raise ValueError(f"Golden case {case.get('id', '<unknown>')} missing {sorted(missing)}")
    return cases


def dense_only(query: str, top_k: int) -> list[dict]:
    return semantic_search(query, top_k=top_k)


def hybrid_rrf(query: str, top_k: int) -> list[dict]:
    candidate_k = top_k * 2
    return rerank_rrf(
        [semantic_search(query, candidate_k), lexical_search(query, candidate_k)],
        top_k=top_k,
        k=60,
    )


def generate_answer(question: str, chunks: list[dict]) -> str:
    if not chunks:
        return SAFE_REFUSAL
    try:
        return call_llm(
            SYSTEM_PROMPT,
            f"Context:\n{format_context(reorder_for_llm(chunks))}\n\nQuestion: {question}",
        ) or SAFE_REFUSAL
    except Exception as error:
        raise RuntimeError(f"Generation failed for question {question!r}: {error}") from error


def produce_rows(name: str, search, cases: list[dict], top_k: int) -> list[dict]:
    rows = []
    for case in cases:
        chunks = search(case["question"], top_k)
        rows.append(
            {
                "id": case["id"],
                "question": case["question"],
                "expected_answer": case["expected_answer"],
                "expected_context": case["expected_context"],
                "answer": generate_answer(case["question"], chunks),
                "contexts": [chunk["content"] for chunk in chunks],
                "source_ids": [chunk["id"] for chunk in chunks],
                "configuration": name,
            }
        )
    return rows


def score_rows(rows: list[dict], evaluator_model: str, evaluator_embedding_model: str) -> tuple[dict, list[dict]]:
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    from ragas import evaluate
    from ragas.dataset_schema import EvaluationDataset, SingleTurnSample
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas.llms import LangchainLLMWrapper
    from ragas.metrics import AnswerRelevancy, Faithfulness, LLMContextPrecisionWithReference, LLMContextRecall

    dataset = EvaluationDataset(
        samples=[
            SingleTurnSample(
                user_input=row["question"],
                response=row["answer"],
                reference=row["expected_answer"],
                retrieved_contexts=row["contexts"],
                reference_contexts=[row["expected_context"]],
            )
            for row in rows
        ]
    )
    llm = LangchainLLMWrapper(ChatOpenAI(model=evaluator_model, temperature=0))
    embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings(model=evaluator_embedding_model))
    result = evaluate(
        dataset=dataset,
        metrics=[Faithfulness(), AnswerRelevancy(), LLMContextRecall(), LLMContextPrecisionWithReference()],
        llm=llm,
        embeddings=embeddings,
        raise_exceptions=True,
        show_progress=True,
    )
    scores = [{key: float(value) for key, value in item.items()} for item in result.scores]
    metric_means = {key: round(mean(item[key] for item in scores), 4) for key in scores[0]}
    return metric_means, [{**row, "metrics": score} for row, score in zip(rows, scores, strict=True)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--limit", type=int, help="Run only the first N cases for a diagnostic smoke test")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    if args.top_k <= 0:
        raise ValueError("--top-k must be positive")

    evaluator_model, evaluator_embedding_model = require_openai_configuration()
    cases = load_cases()
    if args.limit is not None:
        if args.limit <= 0:
            raise ValueError("--limit must be positive")
        cases = cases[: args.limit]
    # Warm the single embedding model before timed/repeated retrieval.
    dense_only(cases[0]["question"], args.top_k)
    rows_a = produce_rows("dense-only", dense_only, cases, args.top_k)
    rows_b = produce_rows("hybrid-rrf", hybrid_rrf, cases, args.top_k)
    metrics_a, scored_a = score_rows(rows_a, evaluator_model, evaluator_embedding_model)
    metrics_b, scored_b = score_rows(rows_b, evaluator_model, evaluator_embedding_model)
    payload = {
        "case_count": len(cases),
        "top_k": args.top_k,
        "generator_model": evaluator_model,
        "evaluator_model": evaluator_model,
        "evaluator_embedding_model": evaluator_embedding_model,
        "config_a": {"name": "dense-only", "metrics": metrics_a, "per_case": scored_a},
        "config_b": {"name": "hybrid-rrf", "metrics": metrics_b, "per_case": scored_b},
        "delta_b_minus_a": {key: round(metrics_b[key] - metrics_a[key], 4) for key in metrics_a},
    }
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"config_a": metrics_a, "config_b": metrics_b, "delta": payload["delta_b_minus_a"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
