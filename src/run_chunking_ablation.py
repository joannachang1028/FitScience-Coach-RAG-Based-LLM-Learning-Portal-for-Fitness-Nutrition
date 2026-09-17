#!/usr/bin/env python3
"""Compare chunk sizes on the fixed 120-case retrieval regression set."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from ragas_evaluation_v3 import CASE_PATH, CORPUS_PATH, RUNS_DIR, collect_actual_runs, load_cases, offline_summary

ROOT = Path(__file__).resolve().parent.parent
CONFIGURATIONS = [
    {"name": "w100_o20", "size_words": 100, "overlap_words": 20,
     "corpus": ROOT / "data" / "chunking_variants" / "evidence_w100_o20.jsonl"},
    {"name": "w180_o35", "size_words": 180, "overlap_words": 35, "corpus": CORPUS_PATH},
    {"name": "w300_o50", "size_words": 300, "overlap_words": 50,
     "corpus": ROOT / "data" / "chunking_variants" / "evidence_w300_o50.jsonl"},
]


def main() -> int:
    cases = load_cases(CASE_PATH)
    if len(cases) < 100:
        raise RuntimeError(f"Expected at least 100 cases, found {len(cases)}")
    results = []
    for configuration in CONFIGURATIONS:
        corpus = configuration["corpus"]
        if not corpus.exists():
            raise FileNotFoundError(f"Missing {corpus}; run python src/build_chunk_variants.py first")
        rows = collect_actual_runs(
            cases,
            enable_reranker=False,
            corpus_path=corpus,
            reference_corpus_path=CORPUS_PATH,
            use_generation=False,
            top_k=4,
            adaptive_top_k=True,
        )
        summary = offline_summary(rows)
        results.append({
            **{key: value for key, value in configuration.items() if key != "corpus"},
            "corpus": str(corpus),
            "chunk_count": sum(1 for line in corpus.read_text().splitlines() if line.strip()),
            "summary": summary,
        })
    artifact = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "evaluation_cases": len(cases),
        "reference_corpus": str(CORPUS_PATH),
        "selection_rule": "Prefer evidence_trigram_f1 while preserving source recall, action accuracy, and latency.",
        "results": results,
    }
    RUNS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = RUNS_DIR / f"chunking_ablation_{timestamp}.json"
    output.write_text(json.dumps(artifact, indent=2) + "\n")
    print(json.dumps(artifact, indent=2))
    print(f"wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
