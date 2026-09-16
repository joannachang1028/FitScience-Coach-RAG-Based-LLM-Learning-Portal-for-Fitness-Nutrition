#!/usr/bin/env python3
"""Download open evidence sources and preserve section-level provenance.

Only openly accessible sources listed in data/evidence_sources.json are ingested.
The output is deliberately a local snapshot: it makes an evaluation reproducible and
prevents the answerer from silently relying on an altered web page at query time.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
SOURCES_PATH = ROOT / "data" / "evidence_sources.json"
OUTPUT_PATH = ROOT / "data" / "evidence_corpus.jsonl"
USER_AGENT = "FitScienceCoach/2.0 educational-research-corpus (+https://github.com/)"


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def chunk_words(text: str, size: int = 180, overlap: int = 35) -> Iterable[str]:
    """Create small, section-preserving chunks; do not split a paragraph mid-word."""
    words = text.split()
    step = max(1, size - overlap)
    for start in range(0, len(words), step):
        chunk = " ".join(words[start : start + size])
        if len(chunk.split()) >= 35:
            yield chunk
        if start + size >= len(words):
            break


def extract_pmc_sections(html: str) -> list[tuple[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    article = soup.select_one("article") or soup.select_one(".article") or soup
    sections: list[tuple[str, str]] = []
    heading = "Abstract"
    paragraphs: list[str] = []
    for node in article.find_all(["h2", "h3", "p"]):
        if node.name in {"h2", "h3"}:
            if paragraphs:
                sections.append((heading, " ".join(paragraphs)))
                paragraphs = []
            heading = clean(node.get_text(" ", strip=True)) or "Untitled section"
        else:
            paragraph = clean(node.get_text(" ", strip=True))
            # Exclude navigation, citations and one-line figure captions.
            if len(paragraph.split()) >= 20 and not paragraph.lower().startswith("copyright"):
                paragraphs.append(paragraph)
    if paragraphs:
        sections.append((heading, " ".join(paragraphs)))
    return sections


def ingest_source(source: dict[str, Any]) -> list[dict[str, Any]]:
    response = requests.get(source["url"], headers={"User-Agent": USER_AGENT}, timeout=30)
    response.raise_for_status()
    sections = extract_pmc_sections(response.text)
    if not sections:
        raise RuntimeError("No article sections extracted")

    downloaded_at = datetime.now(timezone.utc).isoformat()
    records: list[dict[str, Any]] = []
    chunk_number = 0
    for section, text in sections:
        # Reference lists are useful for people but make poor answer context.
        if section.lower() in {"references", "acknowledgments", "author contributions"}:
            continue
        for chunk in chunk_words(text):
            chunk_number += 1
            records.append(
                {
                    "chunk_id": f"{source['source_id']}::c{chunk_number:03d}",
                    "source_id": source["source_id"],
                    "title": source["title"],
                    "url": source["url"],
                    "doi": source.get("doi", ""),
                    "published_year": source["published_year"],
                    "evidence_level": source["evidence_level"],
                    "population": source["population"],
                    "topics": source["topics"],
                    "section": section,
                    "downloaded_at": downloaded_at,
                    "content": chunk,
                }
            )
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", type=Path, default=SOURCES_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()

    sources = json.loads(args.sources.read_text())
    all_records: list[dict[str, Any]] = []
    failures: list[str] = []
    for source in sources:
        try:
            records = ingest_source(source)
            all_records.extend(records)
            print(f"ingested {source['source_id']}: {len(records)} chunks")
        except Exception as exc:  # Keep a partial snapshot usable and make failures explicit.
            failures.append(f"{source['source_id']}: {exc}")
            print(f"failed {source['source_id']}: {exc}")

    if not all_records:
        raise RuntimeError("No sources ingested; evidence corpus was not overwritten")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in all_records) + "\n")
    print(f"wrote {len(all_records)} chunks to {args.output}")
    if failures:
        print("Failures (rerun after checking source availability):")
        print("\n".join(failures))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
