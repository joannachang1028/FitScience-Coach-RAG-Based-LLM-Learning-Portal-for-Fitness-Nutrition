# Controlled RAG Ablations — 2026-09-16

## Experiment contract

- Labels: 20 project-owner-approved semantic seeds, expanded to 120 variants.
- Retrieval experiments: all 120 cases, no paid generation.
- LLM experiments: 20 canonical routing cases; 12 answerable cases judged by
  RAGAS using GPT-4o-mini and `text-embedding-3-small`.
- One variable changed per experiment.
- Gold chunks and references were never supplied to the retriever.
- Results are regression evidence, not clinical validation.

## 1. Chunking

Fixed: all-MiniLM-L6-v2, FAISS + BM25 RRF, adaptive top-4, no reranker.

| Words / overlap | Chunks | Source recall | Evidence recall | Evidence precision | Evidence F1 | p95 ms |
|---|---:|---:|---:|---:|---:|---:|
| 100 / 20 | 704 | 0.889 | 0.185 | 0.248 | 0.208 | 8.4 |
| **180 / 35** | **434** | **0.986** | 0.243 | 0.203 | **0.214** | **6.7** |
| 300 / 50 | 290 | 0.958 | **0.306** | 0.175 | 0.210 | 7.0 |

Decision: retain 180/35. Small chunks were more precise but lost source coverage;
large chunks increased evidence recall but added irrelevant text. The middle size
had the best F1, source recall, and latency balance.

## 2. Embedding

Fixed: 180/35 chunks, FAISS + BM25 RRF, adaptive top-4, no reranker.

| Model | Dims | Source recall | Gold recall | Evidence F1 | p50 ms | Total run s |
|---|---:|---:|---:|---:|---:|---:|
| **all-MiniLM-L6-v2** | 384 | **0.986** | 0.163 | **0.214** | **6.15** | **4.62** |
| all-MiniLM-L12-v2 | 384 | 0.958 | 0.189 | 0.198 | 8.95 | 4.68 |
| distiluse multilingual | 512 | 0.972 | **0.211** | 0.206 | 11.45 | 7.43 |

Decision: retain MiniLM-L6 for the current English workload. The multilingual
model deserves a separate multilingual test set; an English-only set cannot
justify selecting it for future Chinese queries.

## 3. Retrieval and top-k

Fixed: 180/35 chunks, all-MiniLM-L6-v2, metadata preference, no reranker.

| Policy | Mean chunks | Mean words | Source recall | Gold recall | Evidence F1 | p95 ms |
|---|---:|---:|---:|---:|---:|---:|
| Dense top-4 | 4.00 | 548 | 0.972 | 0.144 | 0.185 | 7.0 |
| BM25 top-4 | 4.00 | 613 | 0.986 | 0.199 | 0.208 | 7.0 |
| Hybrid top-2 | 2.00 | 293 | 0.875 | 0.093 | 0.162 | 6.5 |
| Hybrid top-4 | 4.00 | 608 | 0.986 | 0.172 | 0.216 | 6.5 |
| **Hybrid top-6** | **6.00** | **915** | **1.000** | **0.270** | **0.232** | 6.9 |
| Hybrid adaptive 2–4 | 3.56 | 536 | 0.986 | 0.163 | 0.214 | 7.7 |

Decision: use fixed hybrid top-6. Relative to adaptive 2–4, evidence F1 improved
about 8.7% and gold recall about 65%, while local p95 stayed below 7 ms. Prompt
context grew about 71%, so model input cost—not FAISS latency—is the principal
trade-off.

## 4. LLM generation

Fixed: selected chunking, embedding, and hybrid top-6 retrieval.

| Model | Faithfulness | Answer relevance | Context precision | Context recall | Citation pass | p50 |
|---|---:|---:|---:|---:|---:|---:|
| GPT-4o-mini | 1.000 | 0.522 | **0.956** | 0.944 | 0.917 | **1.09 s** |
| **GPT-4.1-mini** | **1.000** | **0.593** | 0.949 | **0.944** | **1.000** | 1.36 s |
| Groq Llama 3.1 8B | invalid | invalid | invalid | invalid | invalid | invalid |
| Groq `gpt-oss-20b` | incomplete | incomplete | incomplete | incomplete | incomplete | rate limited |

The configured Groq Llama ID returned `NotFoundError`; the account model list no
longer offered a general Llama model. The replacement `openai/gpt-oss-20b` was
available but returned HTTP 429 during the controlled run. Corpus-only fallback
outputs from those failures were explicitly excluded from model comparison.

Decision: GPT-4.1-mini is the quality default and GPT-4o-mini is the cost-sensitive
alternative. At experiment time, official list token prices for GPT-4.1-mini were
about 2.67× GPT-4o-mini; p50 latency was about 25% higher. Repeat the evaluation
before treating its 12-case relevance improvement as statistically reliable.

## 5. RAGAS placement

RAGAS was used:

1. after label approval, to establish an actual-context baseline;
2. after selecting retrieval top-k, to catch generation degradation from added
   context;
3. during LLM comparison, with one fixed judge and fixed references.

It was not used to select every chunk or embedding candidate because LLM judging
would add cost and noise to a retrieval-only question. Retrieval candidates were
first filtered with deterministic source, gold-chunk, evidence-overlap, routing,
latency, and context-size metrics.

## 6. Decision on advanced RAG

Do not add agentic RAG yet. The selected single-hop retriever has full expected
source recall on this set and high RAGAS context recall. There are no approved
multi-hop or ambiguous-dialogue labels demonstrating a failure that an agent would
solve. Adding query decomposition now would increase latency, cost, state, and
debugging surface without an evidence-backed acceptance criterion.

Trigger for reconsideration: add reviewed multi-document, ambiguous, and
conversation-dependent cases; if single-hop retrieval then misses necessary
evidence, compare deterministic query rewriting, multi-query retrieval, and only
then agentic planning.
