#!/usr/bin/env python3
"""Validate approved FitScience gold labels before building or evaluating cases."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT / "data" / "evidence_sources.json"
CORPUS_PATH = ROOT / "data" / "evidence_corpus.jsonl"
SEED_PATH = ROOT / "data" / "evaluation_seed_review.jsonl"
GOLD_PATH = ROOT / "data" / "evaluation_gold_seeds.jsonl"


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main() -> None:
    source_ids = {source["source_id"] for source in json.loads(MANIFEST_PATH.read_text())}
    chunks = {row["chunk_id"]: row for row in load_jsonl(CORPUS_PATH)}
    seeds = {row["seed_id"]: row for row in load_jsonl(SEED_PATH)}
    gold_labels = load_jsonl(GOLD_PATH)
    errors: list[str] = []
    seen: set[str] = set()

    for label in gold_labels:
        seed_id = label["seed_id"]
        if seed_id in seen:
            errors.append(f"{seed_id}: duplicate gold label")
        seen.add(seed_id)
        seed = seeds.get(seed_id)
        if not seed:
            errors.append(f"{seed_id}: no matching seed")
            continue
        if label["question"] != seed["question"]:
            errors.append(f"{seed_id}: question differs from seed")
        if label["expected_action"] != seed["expected_action"]:
            errors.append(f"{seed_id}: action differs from reviewed seed")
        if label["label_status"] != "approved" or label["reviewer_decision"] != "accept":
            errors.append(f"{seed_id}: label is not approved")
        if not label["reference_answer"].strip():
            errors.append(f"{seed_id}: missing reference answer")
        if not label["required_claims"]:
            errors.append(f"{seed_id}: missing required claims")

        expected_sources = set(label["expected_source_ids"])
        unknown_sources = expected_sources - source_ids
        if unknown_sources:
            errors.append(f"{seed_id}: unknown sources {sorted(unknown_sources)}")
        if label["expected_action"] == "answerable":
            if not label["gold_chunk_ids"]:
                errors.append(f"{seed_id}: answerable label is missing gold chunks")
            if not expected_sources:
                errors.append(f"{seed_id}: answerable label is missing an expected source")
        elif label["gold_chunk_ids"] or expected_sources:
            errors.append(f"{seed_id}: non-answerable label must not declare retrieval gold")

        for chunk_id in label["gold_chunk_ids"]:
            chunk = chunks.get(chunk_id)
            if not chunk:
                errors.append(f"{seed_id}: unknown chunk {chunk_id}")
            elif chunk["source_id"] not in expected_sources:
                errors.append(
                    f"{seed_id}: chunk {chunk_id} belongs to unexpected source "
                    f"{chunk['source_id']}"
                )

    seed_ids = set(seeds)
    if seen != seed_ids:
        errors.append(
            "gold-label coverage mismatch: "
            f"missing={sorted(seed_ids - seen)}, extra={sorted(seen - seed_ids)}"
        )

    if errors:
        raise SystemExit("Label validation failed:\n- " + "\n- ".join(errors))
    print(
        f"Validated {len(gold_labels)} approved gold labels against "
        f"{len(source_ids)} sources and {len(chunks)} chunks."
    )


if __name__ == "__main__":
    main()
