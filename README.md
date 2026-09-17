# FitScience Coach — Evidence-Grounded RAG

FitScience Coach is a fitness and nutrition education assistant. Its answer path
retrieves from a fixed snapshot of open-access evidence, generates concise claims,
and requires every generated bullet to cite the retrieved passage that supports it.

> This is an engineering portfolio project, not a medical device. Evaluation
> scores are regression metrics on a small human-reviewed set; they are not
> clinical accuracy.

## Current system

```text
User question
  → PII masking + prompt-injection / medical-risk routing
  → coverage check
  → all-MiniLM-L6-v2 query embedding (384 dimensions)
  → FAISS dense retrieval + in-process BM25
  → reciprocal-rank fusion + metadata preference
  → fixed top-6 evidence chunks
  → GPT-4.1-mini grounded generation
  → sentence-level [S1] citation contract
  → JSONL trace + exact in-process cache
```

The retriever indexes 434 section-level chunks from 8 verified PMC articles and
position papers. Chunks preserve source ID, URL, DOI, publication year, evidence
level, population, section, and exact text. The older 23-row curated CSV remains
for the learning-portal UI and project history; it is not part of the current RAG
answer path.

Primary generation uses GPT-4.1-mini when `OPENAI_API_KEY` is configured. Groq
`openai/gpt-oss-20b` is a provider-failure fallback when `GROQ_API_KEY` is also
configured, but its current account rate limit prevented a complete ablation.
Without an available model, the system returns a directly extracted source
sentence rather than inventing an answer.

## Why these defaults

Every experiment used the same approved labels and fixed all variables except the
one named in the table. Full results and limitations are in
[Ablation Results](reports/Ablation_Results_2026-09-16.md).

| Decision | Selected | Observed trade-off |
|---|---|---|
| Chunking | 180 words / 35 overlap | Best evidence F1 and source recall versus 100/20 and 300/50 |
| Embedding | all-MiniLM-L6-v2, 384-d | Best evidence F1/source recall; multilingual model improved strict chunk hits but was slower |
| Retrieval | FAISS + BM25 RRF, fixed top-6 | Full-set source recall 1.000 and evidence F1 0.232; average context grew from 536 to 915 words |
| Generator | GPT-4.1-mini | Better relevance/citation compliance in the 12-case run; about 25% higher p50 latency and 2.67× list token price versus GPT-4o-mini |

No agentic RAG was added. With fixed top-6, source recall reached 1.000 and the
canonical RAGAS context recall reached 0.944. The remaining weaknesses are answer
relevance, small-set uncertainty, a ketogenic-diet coverage boundary, and domain
validation—not evidence that multi-agent orchestration is needed.

## Evaluation

The evaluation set contains 20 human-approved semantic seeds expanded into 120
versioned query variants:

- 12 answerable evidence questions with approved source IDs, gold chunks,
  reference answers, required claims, and disallowed claims;
- 3 insufficient-evidence topics;
- 4 high-risk medical/vulnerable-population questions;
- 1 prompt-injection case.

Latest full 120-case offline retrieval regression with the selected top-6 policy:

| Metric | Result |
|---|---:|
| Action accuracy | 0.950 |
| Expected-source recall@k | 1.000 |
| Gold-chunk recall@k | 0.270 |
| Gold-chunk MRR | 0.321 |
| Chunk-boundary-independent evidence trigram F1 | 0.232 |
| Safe-abstention accuracy | 0.875 |
| Mean retrieved context | 915 words |
| Local retrieval p50 / p95 | 5.9 / 6.9 ms |

Canonical 12-answerable-case RAGAS run for GPT-4.1-mini with actual retrieved
contexts:

| Metric | Result |
|---|---:|
| Faithfulness | 1.000 |
| Answer relevancy | 0.593 |
| Context precision | 0.949 |
| Context recall | 0.944 |

The historical `0.857` under `ragas_results/` evaluated five examples with
prewritten contexts. It is retained as project history but must not be presented
as current retrieval performance or clinical correctness.

## Safety and observability

- Masks email addresses and phone numbers before retrieval and tracing.
- Blocks common prompt-injection phrases before embedding or retrieval.
- Abstains on injury, pregnancy, medications, eating disorders, minors, and other
  high-risk health contexts.
- Rejects topics outside the evidence manifest.
- Records query rewrite, retrieved chunk IDs, retrieval mode, citation-verifier
  result, selected provider/model, estimated token usage, outcome, and latency.
- Requires `[S1]`-style labels on every generated bullet; unsupported or malformed
  lines are removed, with a source-excerpt fallback if no line survives.

## Quick start

```bash
pip install -r requirements.txt

# Optional: refresh source snapshot. The committed snapshot is already usable.
python src/ingest_evidence.py

python src/validate_evaluation_labels.py
python src/build_evaluation_set.py
streamlit run src/streamlit_app.py
```

Create `.env` on the host; never commit it:

```dotenv
OPENAI_API_KEY=...
GROQ_API_KEY=...  # optional fallback
```

## Reproduce the experiments

```bash
# Free, local 120-case regression; --offline disables generation and RAGAS.
python src/ragas_evaluation_v3.py --offline

# Paid canonical run: 20 routing cases, 12 answerable cases judged by RAGAS.
python src/ragas_evaluation_v3.py --canonical-only

# Controlled ablations.
python src/build_chunk_variants.py
python src/run_chunking_ablation.py
python src/run_embedding_ablation.py
python src/run_retrieval_ablation.py
python src/run_llm_ablation.py
```

Runtime traces and detailed evaluation runs are intentionally gitignored. The
versioned summaries live under `reports/`.

## Repository map

```text
data/
  evidence_sources.json          active source manifest
  evidence_corpus.jsonl          434 provenance-preserving chunks
  evaluation_gold_seeds.jsonl    20 approved semantic labels
  evaluation_cases.jsonl         120 regression variants
src/
  rag_pipeline.py                safety, retrieval, generation, citations, trace
  ingest_evidence.py             reproducible PMC ingestion
  build_evaluation_set.py        label expansion
  validate_evaluation_labels.py  gold-label integrity checks
  ragas_evaluation_v3.py         actual-context evaluator
  build_chunk_variants.py        fixed-snapshot re-chunking
  run_*_ablation.py              controlled experiment runners
  streamlit_app.py               learning portal UI
reports/
  Evidence_Source_Audit.md
  Evaluation_Labeling_Guide.md
  Ablation_Results_2026-09-16.md
  RAG_v2_Implementation_and_Baseline.md
```

## Known limitations

- Only 8 active evidence sources and 20 semantic evaluation seeds.
- Gold labels were reviewed by the project owner, not clinicians.
- RAGAS is an LLM-as-judge signal and varies across runs; it complements rather
  than replaces human domain review.
- The ketogenic-diet seed exposes a real manifest-routing false positive, keeping
  action accuracy at 0.950 and safe-abstention accuracy at 0.875.
- GPT-4.1-mini won one small controlled run; a larger repeated evaluation is
  required before calling the difference statistically reliable.
- Groq `gpt-oss-20b` fallback is configured but not quality-approved because the
  current account returned HTTP 429 during its ablation.

## License

Academic portfolio project.
