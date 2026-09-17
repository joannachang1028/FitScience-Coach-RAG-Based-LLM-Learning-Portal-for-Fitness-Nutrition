#!/usr/bin/env python3
"""Build 120 evaluation variants from the human-approved semantic gold seeds.

Approval means the project owner reviewed the evaluation labels. It does not
turn the set into clinical validation or establish clinical accuracy.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "data" / "evaluation_cases.jsonl"
GOLD_SEEDS = ROOT / "data" / "evaluation_gold_seeds.jsonl"

VARIANTS = [
    "{question}",
    "Based only on your evidence sources: {question}",
    "For health education, {question}",
    "Please answer concisely: {question}",
    "What can your research snapshot support about this: {question}",
    "I want a cited answer. {question}",
]


def load_gold_seeds() -> list[dict]:
    seeds = [json.loads(line) for line in GOLD_SEEDS.read_text().splitlines() if line.strip()]
    if len(seeds) != 20:
        raise RuntimeError(f"Expected 20 gold seeds, found {len(seeds)}")
    unapproved = [seed["seed_id"] for seed in seeds if seed["label_status"] != "approved"]
    if unapproved:
        raise RuntimeError(f"Gold seeds require approval: {unapproved}")
    return seeds


def create_cases() -> list[dict]:
    cases = []
    for seed in load_gold_seeds():
        for variant_number, template in enumerate(VARIANTS, start=1):
            cases.append(
                {
                    "case_id": f"{seed['seed_id']}_{variant_number}",
                    "seed_id": seed["seed_id"],
                    "question": template.format(question=seed["question"]),
                    "expected_source_ids": seed["expected_source_ids"],
                    "gold_chunk_ids": seed["gold_chunk_ids"],
                    "reference_answer": seed["reference_answer"],
                    "required_claims": seed["required_claims"],
                    "disallowed_claims": seed["disallowed_claims"],
                    "expected_action": seed["expected_action"],
                    "risk_level": seed["risk_level"],
                    "label_status": seed["label_status"],
                    "label_schema_version": seed["schema_version"],
                }
            )
    return cases


def main() -> None:
    cases = create_cases()
    if len(cases) < 100:
        raise RuntimeError("Evaluation set must contain at least 100 cases")
    OUTPUT.write_text("\n".join(json.dumps(case, ensure_ascii=False) for case in cases) + "\n")
    print(f"Wrote {len(cases)} versioned evaluation cases to {OUTPUT}")


if __name__ == "__main__":
    main()
