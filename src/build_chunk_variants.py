#!/usr/bin/env python3
"""Re-chunk the immutable evidence snapshot without downloading source pages."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

from ingest_evidence import chunk_words

ROOT = Path(__file__).resolve().parent.parent
BASELINE = ROOT / "data" / "evidence_corpus.jsonl"
OUTPUT_DIR = ROOT / "data" / "chunking_variants"


def load_rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def reconstruct_sections(rows: list[dict[str, Any]], baseline_overlap: int = 35) -> list[tuple[dict[str, Any], str]]:
    """Merge contiguous chunks using the baseline's known exact word overlap."""
    sections: list[tuple[dict[str, Any], str]] = []
    current_key: tuple[str, str] | None = None
    metadata: dict[str, Any] | None = None
    words: list[str] = []
    for row in rows:
        key = (row["source_id"], row["section"])
        chunk_words_list = row["content"].split()
        if key != current_key:
            if metadata is not None:
                sections.append((metadata, " ".join(words)))
            current_key = key
            metadata = {field: value for field, value in row.items() if field not in {"chunk_id", "content"}}
            words = chunk_words_list
            continue
        if words[-baseline_overlap:] != chunk_words_list[:baseline_overlap]:
            raise ValueError(f"Unexpected overlap in {row['chunk_id']}; baseline snapshot may not use 180/35 chunking")
        words.extend(chunk_words_list[baseline_overlap:])
    if metadata is not None:
        sections.append((metadata, " ".join(words)))
    return sections


def build_variant(
    sections: Iterable[tuple[dict[str, Any], str]],
    size: int,
    overlap: int,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    source_counts: dict[str, int] = {}
    profile = f"w{size}_o{overlap}"
    for metadata, text in sections:
        source_id = metadata["source_id"]
        for content in chunk_words(text, size=size, overlap=overlap):
            source_counts[source_id] = source_counts.get(source_id, 0) + 1
            records.append({
                "chunk_id": f"{source_id}::{profile}::c{source_counts[source_id]:03d}",
                **metadata,
                "chunk_profile": profile,
                "content": content,
            })
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, default=BASELINE)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--profile", action="append", default=[], help="SIZE:OVERLAP; repeat for multiple variants")
    args = parser.parse_args()
    profiles = args.profile or ["100:20", "300:50"]
    sections = reconstruct_sections(load_rows(args.baseline))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    manifest = []
    for raw_profile in profiles:
        size, overlap = (int(value) for value in raw_profile.split(":", 1))
        if not 35 <= size or not 0 <= overlap < size:
            raise ValueError(f"Invalid chunk profile {raw_profile}")
        records = build_variant(sections, size, overlap)
        path = args.output_dir / f"evidence_w{size}_o{overlap}.jsonl"
        path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in records) + "\n")
        manifest.append({"size_words": size, "overlap_words": overlap, "chunk_count": len(records), "path": str(path)})
        print(f"wrote {len(records)} chunks to {path}")
    (args.output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"reconstructed {len(sections)} contiguous sections from the fixed baseline snapshot")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
