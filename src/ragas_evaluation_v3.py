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
import re
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rag_pipeline import FitScienceRAG

ROOT = Path(__file__).resolve().parent.parent
CASE_PATH = ROOT / "data" / "evaluation_cases.jsonl"
CORPUS_PATH = ROOT / "data" / "evidence_corpus.jsonl"
RUNS_DIR = ROOT / "evaluation_runs"


def load_cases(path: Path = CASE_PATH) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError("Evaluation cases missing; run python src/build_evaluation_set.py.")
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def load_corpus_by_chunk(path: Path = CORPUS_PATH) -> dict[str, dict[str, Any]]:
    return {
        row["chunk_id"]: row
        for row in (json.loads(line) for line in path.read_text().splitlines() if line.strip())
    }


def reciprocal_rank(retrieved_source_ids: list[str], expected_source_ids: list[str]) -> float:
    for rank, source_id in enumerate(retrieved_source_ids, start=1):
        if source_id in expected_source_ids:
            return 1 / rank
    return 0.0


def set_recall(retrieved_ids: list[str], gold_ids: list[str]) -> float | None:
    if not gold_ids:
        return None
    return len(set(retrieved_ids) & set(gold_ids)) / len(set(gold_ids))


def set_precision(retrieved_ids: list[str], gold_ids: list[str]) -> float | None:
    if not gold_ids:
        return None
    if not retrieved_ids:
        return 0.0
    return len(set(retrieved_ids) & set(gold_ids)) / len(set(retrieved_ids))


def text_ngrams(texts: list[str], size: int = 3) -> set[tuple[str, ...]]:
    ngrams: set[tuple[str, ...]] = set()
    for text in texts:
        tokens = re.findall(r"[a-z0-9]+", text.lower())
        ngrams.update(tuple(tokens[index:index + size]) for index in range(max(0, len(tokens) - size + 1)))
    return ngrams


def evidence_overlap(retrieved: list[str], reference: list[str]) -> tuple[float | None, float | None, float | None]:
    """Chunk-boundary-independent overlap against human-approved evidence text."""
    retrieved_ngrams, reference_ngrams = text_ngrams(retrieved), text_ngrams(reference)
    if not reference_ngrams:
        return None, None, None
    overlap = len(retrieved_ngrams & reference_ngrams)
    recall = overlap / len(reference_ngrams)
    precision = overlap / len(retrieved_ngrams) if retrieved_ngrams else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return recall, precision, f1


def action_is_correct(expected: str, result: dict[str, Any]) -> bool:
    if expected == "answerable":
        return result.get("status") == "answered"
    if expected == "insufficient_evidence":
        return result.get("status") == "insufficient_evidence"
    if expected in {"high_risk", "blocked"}:
        return result.get("status") == "abstained"
    return False


def collect_actual_runs(
    cases: list[dict[str, Any]],
    enable_reranker: bool,
    corpus_path: Path = CORPUS_PATH,
    reference_corpus_path: Path = CORPUS_PATH,
    use_generation: bool = True,
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    retrieval_mode: str = "hybrid",
    top_k: int = 6,
    adaptive_top_k: bool = False,
    generation_provider: str = "auto",
    generation_model: str | None = None,
    required_generation_model: str | None = None,
) -> list[dict[str, Any]]:
    corpus_by_chunk = load_corpus_by_chunk(corpus_path)
    reference_by_chunk = load_corpus_by_chunk(reference_corpus_path)
    comparable_chunk_ids = corpus_path.resolve() == reference_corpus_path.resolve()
    if generation_provider not in {"auto", "openai", "groq"}:
        raise ValueError("generation_provider must be auto, openai, or groq")
    openai_key = os.getenv("OPENAI_API_KEY") if use_generation and generation_provider in {"auto", "openai"} else ""
    groq_key = os.getenv("GROQ_API_KEY") if use_generation and generation_provider in {"auto", "groq"} else ""
    rag = FitScienceRAG(
        use_groq=bool(groq_key),
        openai_api_key=openai_key,
        groq_api_key=groq_key,
        enable_reranker=enable_reranker,
        evidence_path=corpus_path,
        embedding_model=embedding_model,
        retrieval_mode=retrieval_mode,
        top_k=top_k,
        adaptive_top_k=adaptive_top_k,
        openai_model=generation_model if generation_provider == "openai" and generation_model else "gpt-4.1-mini",
        groq_model=generation_model if generation_provider == "groq" and generation_model else "openai/gpt-oss-20b",
    )
    if not rag.initialize_system():
        raise RuntimeError("FitScience RAG initialization failed")
    rows = []
    for case in cases:
        started = time.perf_counter()
        result = rag.query(case["question"])
        if (
            required_generation_model
            and case["expected_action"] == "answerable"
            and result.get("generation_model") != required_generation_model
        ):
            raise RuntimeError(
                f"Required {required_generation_model}, received "
                f"{result.get('generation_model', result.get('status', 'error'))}"
            )
        sources = result.get("sources", [])
        retrieved_source_ids = [source["source_id"] for source in sources]
        retrieved_chunk_ids = [source["chunk_id"] for source in sources]
        expected_source_ids = case["expected_source_ids"]
        gold_chunk_ids = case["gold_chunk_ids"]
        retrieved_contexts = [corpus_by_chunk[chunk_id]["content"] for chunk_id in retrieved_chunk_ids]
        reference_contexts = [reference_by_chunk[chunk_id]["content"] for chunk_id in gold_chunk_ids]
        overlap_recall, overlap_precision, overlap_f1 = evidence_overlap(retrieved_contexts, reference_contexts)
        rows.append({
            **case,
            "status": result.get("status", "error"),
            "answer": result.get("answer", result.get("error", "")),
            # The key correction: use passages this query really retrieved.
            "retrieved_contexts": retrieved_contexts,
            "reference_contexts": reference_contexts,
            "retrieved_chunk_ids": retrieved_chunk_ids,
            "retrieved_source_ids": retrieved_source_ids,
            "citation_verifier": result.get("citation_verifier", {}),
            "generation_model": result.get("generation_model"),
            "generation_usage": result.get("generation_usage", {}),
            "latency_ms": round((time.perf_counter() - started) * 1000, 1),
            "action_correct": action_is_correct(case["expected_action"], result),
            "source_recall_at_k": int(bool(set(expected_source_ids) & set(retrieved_source_ids))) if expected_source_ids else None,
            "source_reciprocal_rank": reciprocal_rank(retrieved_source_ids, expected_source_ids) if expected_source_ids else None,
            "gold_chunk_recall_at_k": set_recall(retrieved_chunk_ids, gold_chunk_ids) if comparable_chunk_ids else None,
            "gold_chunk_precision_at_k": set_precision(retrieved_chunk_ids, gold_chunk_ids) if comparable_chunk_ids else None,
            "gold_chunk_reciprocal_rank": reciprocal_rank(retrieved_chunk_ids, gold_chunk_ids) if gold_chunk_ids and comparable_chunk_ids else None,
            "evidence_trigram_recall": overlap_recall,
            "evidence_trigram_precision": overlap_precision,
            "evidence_trigram_f1": overlap_f1,
        })
    return rows


def offline_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    answerable = [row for row in rows if row["expected_action"] == "answerable"]
    abstentions = [row for row in rows if row["expected_action"] != "answerable"]
    source_recalls = [row["source_recall_at_k"] for row in answerable]
    source_ranks = [row["source_reciprocal_rank"] for row in answerable]
    gold_recalls = [row["gold_chunk_recall_at_k"] for row in answerable]
    gold_precisions = [row["gold_chunk_precision_at_k"] for row in answerable]
    gold_ranks = [row["gold_chunk_reciprocal_rank"] for row in answerable]
    evidence_recalls = [row["evidence_trigram_recall"] for row in answerable]
    evidence_precisions = [row["evidence_trigram_precision"] for row in answerable]
    evidence_f1s = [row["evidence_trigram_f1"] for row in answerable]
    citation_passes = [row["citation_verifier"].get("status") == "passed" for row in answerable if row["status"] == "answered"]
    latencies = sorted(row["latency_ms"] for row in rows)
    generation_models = sorted({row["generation_model"] for row in answerable if row.get("generation_model")})
    retrieved_counts = [len(row["retrieved_chunk_ids"]) for row in answerable]
    context_word_counts = [sum(len(context.split()) for context in row["retrieved_contexts"]) for row in answerable]
    usage_totals = {
        key: sum(row.get("generation_usage", {}).get(key, 0) for row in answerable)
        for key in ("input_tokens", "output_tokens", "total_tokens")
    }
    usage_totals["estimated"] = any(row.get("generation_usage", {}).get("estimated", False) for row in answerable)
    return {
        "case_count": len(rows),
        "label_status": "Human-approved regression labels; not clinical validation or clinical accuracy.",
        "generation_models": generation_models,
        "mean_retrieved_chunks": statistics.fmean(retrieved_counts) if retrieved_counts else None,
        "mean_retrieved_context_words": statistics.fmean(context_word_counts) if context_word_counts else None,
        "generation_usage": usage_totals,
        "action_accuracy": sum(row["action_correct"] for row in rows) / len(rows),
        "source_recall_at_k": statistics.fmean(source_recalls) if source_recalls else None,
        "source_mrr": statistics.fmean(source_ranks) if source_ranks else None,
        "gold_chunk_recall_at_k": statistics.fmean(value for value in gold_recalls if value is not None) if any(value is not None for value in gold_recalls) else None,
        "gold_chunk_precision_at_k": statistics.fmean(value for value in gold_precisions if value is not None) if any(value is not None for value in gold_precisions) else None,
        "gold_chunk_mrr": statistics.fmean(value for value in gold_ranks if value is not None) if any(value is not None for value in gold_ranks) else None,
        "evidence_trigram_recall": statistics.fmean(value for value in evidence_recalls if value is not None) if any(value is not None for value in evidence_recalls) else None,
        "evidence_trigram_precision": statistics.fmean(value for value in evidence_precisions if value is not None) if any(value is not None for value in evidence_precisions) else None,
        "evidence_trigram_f1": statistics.fmean(value for value in evidence_f1s if value is not None) if any(value is not None for value in evidence_f1s) else None,
        "citation_contract_pass_rate": sum(citation_passes) / len(citation_passes) if citation_passes else None,
        "safe_abstention_accuracy": sum(row["action_correct"] for row in abstentions) / len(abstentions) if abstentions else None,
        "p50_latency_ms": statistics.median(latencies),
        "p95_latency_ms": latencies[max(0, math.ceil(len(latencies) * .95) - 1)],
    }


def run_ragas_on_actual_contexts(rows: list[dict[str, Any]], all_variants: bool = False) -> dict[str, Any]:
    """Optional LLM-as-judge evaluation, safely skipped if key/deps are unavailable."""
    if not os.getenv("OPENAI_API_KEY"):
        return {"status": "skipped", "reason": "OPENAI_API_KEY is not configured."}
    try:
        from datasets import Dataset
        from langchain_openai import ChatOpenAI, OpenAIEmbeddings
        from ragas import evaluate
        from ragas.metrics import AnswerRelevancy, ContextPrecision, ContextRecall, Faithfulness
    except ImportError as exc:
        print(f"RAGAS skipped: missing optional dependency ({exc})")
        return {"status": "skipped", "reason": f"Missing optional dependency: {exc}"}
    evaluable = [
        row for row in rows
        if row["expected_action"] == "answerable"
        and row["retrieved_contexts"]
        and (all_variants or row["case_id"].endswith("_1"))
    ]
    if not evaluable:
        return {"status": "skipped", "reason": "No answerable cases with retrieved contexts."}
    dataset = Dataset.from_dict({
        "question": [row["question"] for row in evaluable],
        "answer": [row["answer"] for row in evaluable],
        "contexts": [row["retrieved_contexts"] for row in evaluable],
        "ground_truth": [row["reference_answer"] for row in evaluable],
    })
    result = evaluate(
        dataset,
        metrics=[Faithfulness(), AnswerRelevancy(), ContextPrecision(), ContextRecall()],
        llm=ChatOpenAI(model="gpt-4o-mini", temperature=0),
        embeddings=OpenAIEmbeddings(model="text-embedding-3-small"),
    )
    # RAGAS 0.1 exposes per-row values as ``result.scores``; some later
    # releases expose the same mapping as ``_scores_dict``.
    if hasattr(result, "_scores_dict"):
        score_columns = result._scores_dict
    else:
        score_columns = {metric: result.scores[metric] for metric in result.scores.column_names}
    aggregate = {}
    for metric, values in score_columns.items():
        clean_values = [float(value) for value in values if value is not None and not math.isnan(float(value))]
        aggregate[metric] = statistics.fmean(clean_values) if clean_values else None
    per_case = []
    for index, row in enumerate(evaluable):
        scores = {}
        for metric, values in score_columns.items():
            value = values[index]
            scores[metric] = None if value is None or math.isnan(float(value)) else float(value)
        per_case.append({"case_id": row["case_id"], "seed_id": row["seed_id"], "scores": scores})
    return {
        "status": "completed",
        "case_count": len(evaluable),
        "scope": "all_answerable_variants" if all_variants else "canonical_answerable_seeds",
        "judge_model": "gpt-4o-mini",
        "judge_embeddings": "text-embedding-3-small",
        "metrics": aggregate,
        "per_case": per_case,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reranker", action="store_true", help="Enable optional cross-encoder reranking.")
    parser.add_argument("--offline", action="store_true", help="Disable paid generation and RAGAS judging.")
    parser.add_argument("--corpus", type=Path, default=CORPUS_PATH, help="Corpus used by the retriever.")
    parser.add_argument("--reference-corpus", type=Path, default=CORPUS_PATH, help="Baseline corpus containing approved gold chunks.")
    parser.add_argument("--embedding-model", default="sentence-transformers/all-MiniLM-L6-v2")
    parser.add_argument("--retrieval-mode", choices=["dense", "bm25", "hybrid"], default="hybrid")
    parser.add_argument("--top-k", type=int, default=6)
    parser.add_argument("--adaptive-top-k", action="store_true", help="Allow a strong first result to reduce the context to two chunks.")
    parser.add_argument("--generation-provider", choices=["auto", "openai", "groq"], default="auto")
    parser.add_argument("--generation-model")
    parser.add_argument(
        "--canonical-only",
        action="store_true",
        help="Evaluate one canonical case per seed (20 total) to avoid paying for duplicate paraphrases.",
    )
    parser.add_argument("--ragas-all-variants", action="store_true", help="Judge all answerable paraphrases instead of one canonical case per seed.")
    args = parser.parse_args()
    cases = load_cases()
    if args.canonical_only:
        cases = [case for case in cases if case["case_id"].endswith("_1")]
        if len(cases) != 20:
            raise RuntimeError(f"Expected 20 canonical seed cases, found {len(cases)}")
    elif len(cases) < 100:
        raise RuntimeError(f"Expected at least 100 cases, found {len(cases)}")
    rows = collect_actual_runs(
        cases,
        enable_reranker=args.reranker,
        corpus_path=args.corpus,
        reference_corpus_path=args.reference_corpus,
        use_generation=not args.offline,
        embedding_model=args.embedding_model,
        retrieval_mode=args.retrieval_mode,
        top_k=args.top_k,
        adaptive_top_k=args.adaptive_top_k,
        generation_provider=args.generation_provider,
        generation_model=args.generation_model,
    )
    summary = offline_summary(rows)
    summary["retrieval_corpus"] = str(args.corpus)
    summary["reference_corpus"] = str(args.reference_corpus)
    summary["embedding_model"] = args.embedding_model
    summary["retrieval_mode"] = args.retrieval_mode
    summary["top_k"] = args.top_k
    summary["adaptive_top_k"] = args.adaptive_top_k
    summary["requested_generation_provider"] = args.generation_provider
    summary["requested_generation_model"] = args.generation_model
    if not args.offline:
        summary["ragas_actual_context_metrics"] = run_ragas_on_actual_contexts(
            rows, all_variants=args.ragas_all_variants
        )
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    RUNS_DIR.mkdir(exist_ok=True)
    (RUNS_DIR / f"run_{timestamp}.json").write_text(json.dumps({"summary": summary, "rows": rows}, indent=2))
    (RUNS_DIR / "latest_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
