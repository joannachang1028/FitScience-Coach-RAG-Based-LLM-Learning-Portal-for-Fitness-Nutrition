#!/usr/bin/env python3
"""Compare answer models on identical canonical cases and retrieved evidence."""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone

from ragas_evaluation_v3 import (
    CASE_PATH,
    CORPUS_PATH,
    RUNS_DIR,
    collect_actual_runs,
    load_cases,
    offline_summary,
    run_ragas_on_actual_contexts,
)

MODELS = [
    {"name": "gpt_4o_mini", "provider": "openai", "model": "gpt-4o-mini",
     "input_usd_per_million": 0.15, "output_usd_per_million": 0.60},
    {"name": "gpt_4_1_mini", "provider": "openai", "model": "gpt-4.1-mini",
     "input_usd_per_million": 0.40, "output_usd_per_million": 1.60},
    {"name": "groq_gpt_oss_20b", "provider": "groq", "model": "openai/gpt-oss-20b",
     "input_usd_per_million": None, "output_usd_per_million": None},
]


def estimated_cost(summary: dict, configuration: dict) -> float | None:
    if configuration["input_usd_per_million"] is None:
        return None
    usage = summary["generation_usage"]
    return round(
        usage["input_tokens"] * configuration["input_usd_per_million"] / 1_000_000
        + usage["output_tokens"] * configuration["output_usd_per_million"] / 1_000_000,
        6,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", choices=[configuration["name"] for configuration in MODELS])
    args = parser.parse_args()
    cases = [case for case in load_cases(CASE_PATH) if case["case_id"].endswith("_1")]
    if len(cases) != 20:
        raise RuntimeError(f"Expected 20 canonical cases, found {len(cases)}")
    results = []
    selected_models = [configuration for configuration in MODELS if not args.only or configuration["name"] == args.only]
    for configuration in selected_models:
        started = time.perf_counter()
        expected_model = f"{configuration['provider']}:{configuration['model']}"
        try:
            rows = collect_actual_runs(
                cases,
                enable_reranker=False,
                corpus_path=CORPUS_PATH,
                reference_corpus_path=CORPUS_PATH,
                use_generation=True,
                retrieval_mode="hybrid",
                top_k=6,
                adaptive_top_k=False,
                generation_provider=configuration["provider"],
                generation_model=configuration["model"],
                required_generation_model=expected_model,
            )
        except RuntimeError as exc:
            results.append({
                **configuration,
                "status": "unavailable",
                "reason": str(exc),
                "wall_time_seconds_including_model_and_index": round(time.perf_counter() - started, 3),
            })
            continue
        summary = offline_summary(rows)
        summary["estimated_generation_cost_usd"] = estimated_cost(summary, configuration)
        completed = summary["generation_models"] == [expected_model]
        result = {
            **configuration,
            "status": "completed" if completed else "unavailable",
            "wall_time_seconds_including_index_generation_and_judging": None,
            "summary": summary,
            "samples": [
                {
                    "case_id": row["case_id"],
                    "answer": row["answer"],
                    "generation_model": row["generation_model"],
                    "generation_usage": row["generation_usage"],
                    "latency_ms": row["latency_ms"],
                    "citation_verifier": row["citation_verifier"],
                }
                for row in rows if row["expected_action"] == "answerable"
            ],
            "ragas": run_ragas_on_actual_contexts(rows) if completed else {
                "status": "skipped",
                "reason": f"Requested {expected_model}, received {summary['generation_models']}",
            },
        }
        results.append(result)
        results[-1]["wall_time_seconds_including_index_generation_and_judging"] = round(
            time.perf_counter() - started, 3
        )
    artifact = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "evaluation_cases": len(cases),
        "ragas_answerable_cases_per_model": 12,
        "fixed_configuration": "180/35 chunks; all-MiniLM-L6-v2; hybrid fixed top-6; same approved references; GPT-4o-mini judge",
        "pricing_note": "OpenAI list prices captured from official model pages on 2026-09-16; Groq cost not estimated.",
        "results": results,
    }
    RUNS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = RUNS_DIR / f"llm_ablation_{timestamp}.json"
    output.write_text(json.dumps(artifact, indent=2) + "\n")
    print(json.dumps(artifact, indent=2))
    print(f"wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
