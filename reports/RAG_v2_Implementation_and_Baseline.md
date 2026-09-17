# FitScience RAG v2 — Implementation and Evaluation Baseline

## Scope

The v1 prototype mapped source metadata to synthetic text. The current answer path
uses a reproducible snapshot of 434 section-level chunks from 8 verified,
open-access evidence sources. Two mismatched PMC records were disabled during the
source audit. The separate 23-row curated CSV still supports legacy learning-portal
content but is not indexed by this RAG path.

Each active chunk stores a stable identifier, source ID, title, exact URL, DOI,
publication year, evidence level, population, topic metadata, section, ingestion
timestamp, and source text.

## Runtime design

The query path performs:

1. PII masking;
2. prompt-injection and high-risk medical routing;
3. evidence-manifest coverage checking;
4. local all-MiniLM-L6-v2 embedding;
5. FAISS dense and BM25 lexical retrieval;
6. reciprocal-rank fusion with metadata preference;
7. fixed top-6 evidence selection;
8. GPT-4.1-mini evidence-only generation;
9. claim-level `[S#]` citation verification;
10. exact cache and JSONL trace recording.

Groq `openai/gpt-oss-20b` is configured as a provider-failure fallback. It is not
yet quality-approved because the current Groq account returned HTTP 429 during the
controlled ablation. If no generation provider succeeds, the pipeline uses a
retrieved source sentence and records `corpus-only` as the generation model.

## Evaluation correction

The historical evaluator supplied prewritten contexts to RAGAS. The corrected
evaluator always captures the chunks retrieved by the running system and gives
only those chunks to RAGAS. Approved gold chunks remain references, never inputs to
retrieval.

The versioned set has 20 project-owner-approved semantic seeds expanded into 120
query variants. It covers answerable questions, insufficient evidence, medical
and vulnerable-population abstention, and prompt injection. These are regression
labels, not clinical validation.

Changing chunk boundaries makes exact chunk IDs incomparable. The evaluator
therefore adds evidence trigram recall/precision/F1 against the approved gold text.
Exact gold-chunk metrics are reported only when retrieval and reference corpora
share the same chunk IDs.

## Selected offline baseline

Run date: 2026-09-16

Cases: all 120 variants

Configuration: 180/35 chunks, MiniLM-L6 embeddings, FAISS + BM25 RRF, fixed top-6,
no cross-encoder, corpus-only generation.

| Metric | Result |
|---|---:|
| Action accuracy | 0.950 |
| Source recall@k | 1.000 |
| Source MRR | 0.885 |
| Gold-chunk recall@k | 0.270 |
| Gold-chunk precision@k | 0.130 |
| Gold-chunk MRR | 0.321 |
| Evidence trigram recall | 0.343 |
| Evidence trigram precision | 0.181 |
| Evidence trigram F1 | 0.232 |
| Citation-contract pass rate | 1.000 |
| Safe-abstention accuracy | 0.875 |
| Mean retrieved context | 915 words |
| p50 / p95 local latency | 5.9 / 6.9 ms |

The routing miss is the deliberately retained ketogenic-diet boundary: broad
`diet` coverage admits the query even though the active snapshot does not contain
sufficient ketogenic-diet evidence.

## Canonical actual-context RAGAS

The LLM comparison used one canonical case per semantic seed. Twelve answerable
cases were judged with GPT-4o-mini and `text-embedding-3-small`; non-answerable
cases were scored by deterministic routing metrics.

| Generator | Faithfulness | Answer relevancy | Context precision | Context recall | Citation pass | p50 latency |
|---|---:|---:|---:|---:|---:|---:|
| GPT-4o-mini | 1.000 | 0.522 | 0.956 | 0.944 | 0.917 | 1.09 s |
| GPT-4.1-mini | 1.000 | 0.593 | 0.949 | 0.944 | 1.000 | 1.36 s |

GPT-4.1-mini is the quality default because it improved relevance and citation
contract compliance in this run. Its official list prices at the time of the test
were about 2.67 times GPT-4o-mini for both input and output tokens. The set is too
small for a statistical superiority claim; GPT-4o-mini remains the cost-sensitive
alternative.

## Advanced RAG decision

No agentic RAG, LLM query rewriting, or multi-query retrieval was added. Fixed
top-6 already reached source recall 1.000 on the full set and RAGAS context recall
0.944 on canonical answerable cases. The current constraint is answer relevance
and evaluation breadth, not an observed inability to find multi-document evidence.

The next valid work is repeated evaluation, domain-expert review, and resolving
coverage routing. Advanced retrieval should be introduced only with new multi-hop,
ambiguous, or conversation-dependent labels that demonstrate a single-hop failure.

## Reproducible commands

```bash
python src/validate_evaluation_labels.py
python src/build_evaluation_set.py
python src/ragas_evaluation_v3.py --offline
python src/ragas_evaluation_v3.py --canonical-only
python src/build_chunk_variants.py
python src/run_chunking_ablation.py
python src/run_embedding_ablation.py
python src/run_retrieval_ablation.py
python src/run_llm_ablation.py
```

Do not aggregate the metrics above into a clinical-accuracy percentage. RAGAS is
an LLM-as-judge signal and should be interpreted with per-case review and repeated
runs.
