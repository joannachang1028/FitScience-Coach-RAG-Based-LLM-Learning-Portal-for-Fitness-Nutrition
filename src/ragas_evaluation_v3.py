#!/usr/bin/env python3
"""Evaluate actual FitScience retrieval results, never supplied contexts.

Run 'python src/build_evaluation_set.py' once, then run this script with
'--offline'. Set OPENAI_API_KEY to additionally run RAGAS on actual passages.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rag_pipeline import FitScienceRAG

ROOT = Path(__file__).resolve().parent.parent
CASE_PATH = ROOT / "data" / "evaluation_cases.jsonl"
RUNS_DIR = ROOT / "evaluation_runs"


def load_cases(path: Path = CASE_PATH) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError("Evaluation cases missing; run python src/build_evaluation_set.py.")
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def reciprocal_rank(retrieved_source_ids: list[str], expected_source_ids: list[str]) -> float:
    for rank, source_id in enumerate(retrieved_source_ids, start=1):
        if source_id in expected_source_ids:
            return 1 / rank
    return 0.0


def action_is_correct(expected: str, result: dict[str, Any]) -> bool:
    if expected == "answerable":
        return result.get("status") == "answered"
    if expected == "insufficient_evidence":
        return result.get("status") == "insufficient_evidence"
    if expected in {"high_risk", "blocked"}:
        return result.get("status") == "abstained"
    return False


def collect_actual_runs(cases: list[dict[str, Any]], enable_reranker: bool) -> list[dict[str, Any]]:
    rag = FitScienceRAG(
        use_groq=True,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        groq_api_key=os.getenv("GROQ_API_KEY"),
        enable_reranker=enable_reranker,
    )
    if not rag.initialize_system():
        raise RuntimeError("FitScience RAG initialization failed")
    rows = []
    for case in cases:
        started = time.perf_counter()
        result = rag.query(case["question"])
        sources = result.get("sources", [])
        retrieved_ids, expected_ids = [source["source_id"] for source in sources], case["expected_source_ids"]
        rows.append({
            **case,
            "status": result.get("status", "error"),
            "answer": result.get("answer", result.get("error", "")),
            # The key correction: use passages this query really retrieved.
            "retrieved_contexts": [source["content_preview"] for source in sources],
            "retrieved_chunk_ids": [source["chunk_id"] for source in sources],
            "retrieved_source_ids": retrieved_ids,
            "citation_verifier": result.get("citation_verifier", {}),
            "latency_ms": round((time.perf_counter() - started) * 1000, 1),
            "action_correct": action_is_correct(case["expected_action"], result),
            "retrieval_recall_at_k": int(bool(set(expected_ids) & set(retrieved_ids))) if expected_ids else None,
            "reciprocal_rank": reciprocal_rank(retrieved_ids, expected_ids) if expected_ids else None,
        })
    return rows


def offline_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    answerable = [row for row in rows if row["expected_action"] == "answerable"]
    abstentions = [row for row in rows if row["expected_action"] != "answerable"]
    recalls, ranks = [row["retrieval_recall_at_k"] for row in answerable], [row["reciprocal_rank"] for row in answerable]
    citation_passes = [row["citation_verifier"].get("status") == "passed" for row in answerable if row["status"] == "answered"]
    latencies = sorted(row["latency_ms"] for row in rows)
    return {
        "case_count": len(rows),
        "label_warning": "Draft labels require domain review; these are not clinical-accuracy claims.",
        "action_accuracy": sum(row["action_correct"] for row in rows) / len(rows),
        "retrieval_recall_at_k": sum(recalls) / len(recalls) if recalls else None,
        "mrr": sum(ranks) / len(ranks) if ranks else None,
        "citation_contract_pass_rate": sum(citation_passes) / len(citation_passes) if citation_passes else None,
        "safe_abstention_accuracy": sum(row["action_correct"] for row in abstentions) / len(abstentions) if abstentions else None,
        "p50_latency_ms": statistics.median(latencies),
        "p95_latency_ms": latencies[max(0, math.ceil(len(latencies) * .95) - 1)],
    }


def run_ragas_on_actual_contexts(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Optional LLM-as-judge evaluation, safely skipped if key/deps are unavailable."""
    if not os.getenv("OPENAI_API_KEY"):
        return None
    try:
        from datasets import Dataset
        from langchain_openai import ChatOpenAI, OpenAIEmbeddings
        from ragas import evaluate
        from ragas.metrics import AnswerRelevancy, ContextPrecision, Faithfulness
    except ImportError as exc:
        print(f"RAGAS skipped: missing optional dependency ({exc})")
        return None
    evaluable = [row for row in rows if row["expected_action"] == "answerable" and row["retrieved_contexts"]]
    if not evaluable:
        return None
    dataset = Dataset.from_dict({
        "question": [row["question"] for row in evaluable],
        "answer": [row["answer"] for row in evaluable],
        "contexts": [row["retrieved_contexts"] for row in evaluable],
    })
    result = evaluate(
        dataset,
        metrics=[Faithfulness(), AnswerRelevancy(), ContextPrecision()],
        llm=ChatOpenAI(model="gpt-4o-mini", temperature=0),
        embeddings=OpenAIEmbeddings(model="text-embedding-3-small"),
    )
    return {metric: float(values[0]) for metric, values in result._scores_dict.items()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reranker", action="store_true", help="Enable optional cross-encoder reranking.")
    parser.add_argument("--offline", action="store_true", help="Skip paid RAGAS judging.")
    args = parser.parse_args()
    cases = load_cases()
    if len(cases) < 100:
        raise RuntimeError(f"Expected at least 100 cases, found {len(cases)}")
    rows = collect_actual_runs(cases, enable_reranker=args.reranker)
    summary = offline_summary(rows)
    if not args.offline:
        summary["ragas_actual_context_metrics"] = run_ragas_on_actual_contexts(rows)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    RUNS_DIR.mkdir(exist_ok=True)
    (RUNS_DIR / f"run_{timestamp}.json").write_text(json.dumps({"summary": summary, "rows": rows}, indent=2))
    (RUNS_DIR / "latest_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
