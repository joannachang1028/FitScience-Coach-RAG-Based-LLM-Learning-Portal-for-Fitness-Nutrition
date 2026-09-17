#!/usr/bin/env python3
"""Compare cached embedding models while holding retrieval policy constant."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone

from ragas_evaluation_v3 import CASE_PATH, CORPUS_PATH, RUNS_DIR, collect_actual_runs, load_cases, offline_summary

MODELS = [
    {"name": "minilm_l6", "model": "sentence-transformers/all-MiniLM-L6-v2", "dimensions": 384},
    {"name": "minilm_l12", "model": "sentence-transformers/all-MiniLM-L12-v2", "dimensions": 384},
    {"name": "distiluse_multilingual", "model": "sentence-transformers/distiluse-base-multilingual-cased-v1", "dimensions": 512},
]


def main() -> int:
    cases = load_cases(CASE_PATH)
    if len(cases) < 100:
        raise RuntimeError(f"Expected at least 100 cases, found {len(cases)}")
    results = []
    for configuration in MODELS:
        started = time.perf_counter()
        rows = collect_actual_runs(
            cases,
            enable_reranker=False,
            corpus_path=CORPUS_PATH,
            reference_corpus_path=CORPUS_PATH,
            use_generation=False,
            embedding_model=configuration["model"],
            top_k=4,
            adaptive_top_k=True,
        )
        results.append({
            **configuration,
            "wall_time_seconds_including_model_and_index": round(time.perf_counter() - started, 3),
            "summary": offline_summary(rows),
        })
    artifact = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "evaluation_cases": len(cases),
        "fixed_configuration": "180/35 chunks; FAISS + BM25 RRF; adaptive top-k; no reranker; corpus-only generation",
        "selection_rule": "Prefer evidence F1 and source recall; use latency and dimensions as tie-breakers.",
        "results": results,
    }
    RUNS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = RUNS_DIR / f"embedding_ablation_{timestamp}.json"
    output.write_text(json.dumps(artifact, indent=2) + "\n")
    print(json.dumps(artifact, indent=2))
    print(f"wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
