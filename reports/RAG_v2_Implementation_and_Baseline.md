# FitScience RAG v2 — Evidence, Retrieval, and Evaluation Baseline

## What changed

The v1 prototype mapped source metadata to synthetic text. v2 replaces that path
with a reproducible snapshot of 503 section-level chunks from 10 open-access PMC
articles and position papers. Each chunk carries a stable chunk identifier, source
URL, DOI, publication year, evidence level, population, and article section.

The query path now performs PII masking, injection detection, medical-risk and
coverage routing; conversational query rewriting; dense FAISS plus lexical BM25
retrieval with reciprocal-rank fusion; metadata preference and adaptive context
count; optional cross-encoder reranking; a citation contract; and JSONL tracing.

Generation uses a small gateway policy: configured GPT-4o-mini is primary and a
configured Groq model is invoked only after an OpenAI generation failure. Exact
question results are cached in-process. The selected provider and cache outcome
are included in the trace.

Every generated bullet must cite an exact retrieved source label such as [S1].
A lightweight lexical support check rejects malformed or unsupported lines and
falls back to a source excerpt when needed.

## Evaluation correction

The old evaluator supplied hand-written contexts to RAGAS. That measured a
hypothetical context, not the passages the system retrieved. The v2 evaluator
stores retrieved contexts from each actual query response and supplies only those
to optional RAGAS judging.

The 120 versioned draft cases cover answerable retrieval, unavailable topics,
high-risk health questions, and prompt injection. They are regression labels, not
clinical validation, and require dietitian or clinician review before any
clinical-quality claim.

## Latest offline baseline

Run date: 2026-09-16
Configuration: MiniLM embeddings, FAISS plus in-process BM25 reciprocal-rank
fusion, no cross-encoder, corpus-only generation (no API key).

| Metric | Result | Interpretation |
|---|---:|---|
| Cases | 120 | Draft, versioned regression set |
| Action accuracy | 0.950 | Answer / abstain routing behavior |
| Retrieval recall@k | 0.889 | Expected source appeared in actual retrieval |
| MRR | 0.821 | Expected source ranking |
| Citation contract pass rate | 1.000 | Format/support gate passed in this corpus-only run |
| Safe-abstention accuracy | 0.875 | Known edge: ketogenic-diet questions overlap broad diet coverage |
| p50 / p95 local retrieval latency | 6.0 / 7.2 ms | Excludes cold start and LLM latency |

The ketogenic-diet edge is intentionally retained as a real coverage-boundary
trade-off. Broad topic labels increase recall; narrower labels reduce potentially
misleading answers. The next experiment should compare a fine-grained source
coverage classifier with this conservative manifest without changing the test set.

## Retrieval ablation: optional cross-encoder reranker

The same 120 cases were rerun with cross-encoder/ms-marco-MiniLM-L-6-v2 enabled.
Only reranking changed.

| Configuration | Recall@k | MRR | p50 latency | p95 latency |
|---|---:|---:|---:|---:|
| Hybrid FAISS + BM25 RRF | 0.889 | 0.821 | 6.0 ms | 7.2 ms |
| Hybrid + cross-encoder reranker | 0.861 | 0.792 | 100.9 ms | 139.4 ms |

On this small, draft-labelled corpus, reranking lowered both retrieval measures
and added about 20x p50 latency. It is therefore disabled by default. This is a
decision based on a controlled experiment, not a claim that reranking is generally
harmful; repeat the ablation after expanding and clinician-reviewing the set.

## Reproducible commands

    python src/ingest_evidence.py
    python src/build_evaluation_set.py
    python src/ragas_evaluation_v3.py --offline
    python src/ragas_evaluation_v3.py --reranker --offline

Set OPENAI_API_KEY before running without --offline to add RAGAS Faithfulness,
Answer Relevancy, and Context Precision on actual retrieved contexts. Do not
aggregate those scores into a clinical-accuracy percentage.
