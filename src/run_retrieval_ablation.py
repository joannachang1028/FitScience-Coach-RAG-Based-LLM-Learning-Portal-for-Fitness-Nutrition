#!/usr/bin/env python3
"""Compare dense, BM25, hybrid, and hybrid top-k retrieval policies."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone

from ragas_evaluation_v3 import CASE_PATH, CORPUS_PATH, RUNS_DIR, collect_actual_runs, load_cases, offline_summary

CONFIGURATIONS = [
    {"name": "dense_top4", "retrieval_mode": "dense", "top_k": 4, "adaptive_top_k": False},
    {"name": "bm25_top4", "retrieval_mode": "bm25", "top_k": 4, "adaptive_top_k": False},
    {"name": "hybrid_top2", "retrieval_mode": "hybrid", "top_k": 2, "adaptive_top_k": False},
    {"name": "hybrid_top4", "retrieval_mode": "hybrid", "top_k": 4, "adaptive_top_k": False},
    {"name": "hybrid_top6", "retrieval_mode": "hybrid", "top_k": 6, "adaptive_top_k": False},
    {"name": "hybrid_adaptive_2_4", "retrieval_mode": "hybrid", "top_k": 4, "adaptive_top_k": True},
]


def main() -> int:
    cases = load_cases(CASE_PATH)
    if len(cases) < 100:
        raise RuntimeError(f"Expected at least 100 cases, found {len(cases)}")
    results = []
    for configuration in CONFIGURATIONS:
        started = time.perf_counter()
        rows = collect_actual_runs(
            cases,
            enable_reranker=False,
            corpus_path=CORPUS_PATH,
            reference_corpus_path=CORPUS_PATH,
            use_generation=False,
            retrieval_mode=configuration["retrieval_mode"],
            top_k=configuration["top_k"],
            adaptive_top_k=configuration["adaptive_top_k"],
        )
        results.append({
            **configuration,
            "wall_time_seconds_including_model_and_index": round(time.perf_counter() - started, 3),
            "summary": offline_summary(rows),
        })
    artifact = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "evaluation_cases": len(cases),
        "fixed_configuration": "180/35 chunks; all-MiniLM-L6-v2; metadata preference; no reranker; corpus-only generation",
        "selection_rule": "Prefer evidence F1 and source recall while minimizing context count and latency.",
        "results": results,
    }
    RUNS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = RUNS_DIR / f"retrieval_ablation_{timestamp}.json"
    output.write_text(json.dumps(artifact, indent=2) + "\n")
    print(json.dumps(artifact, indent=2))
    print(f"wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
