# FitScience Coach — Current Architecture

## Runtime request path

```text
┌──────────────┐
│ Streamlit UI │
└──────┬───────┘
       ▼
┌───────────────────────────────────────────────┐
│ Input controls                                │
│ • mask email / phone                          │
│ • block prompt injection                      │
│ • abstain on high-risk health questions       │
│ • reject topics outside evidence manifest     │
└──────┬────────────────────────────────────────┘
       ▼
┌───────────────────────────────────────────────┐
│ Hybrid retrieval                              │
│ • all-MiniLM-L6-v2 query embedding (384-d)    │
│ • FAISS dense candidates                      │
│ • BM25 lexical candidates                     │
│ • reciprocal-rank fusion                      │
│ • metadata preference                         │
│ • fixed top-6 evidence chunks                 │
└──────┬────────────────────────────────────────┘
       ▼
┌───────────────────────────────────────────────┐
│ Generation                                    │
│ • primary: OpenAI GPT-4.1-mini                │
│ • provider fallback: Groq gpt-oss-20b         │
│ • final fallback: retrieved source sentence   │
└──────┬────────────────────────────────────────┘
       ▼
┌───────────────────────────────────────────────┐
│ Output contract                               │
│ • 1–4 concise bullets                         │
│ • every bullet ends with [S#]                 │
│ • unsupported/malformed claims removed        │
└──────┬────────────────────────────────────────┘
       ▼
┌───────────────────────────────────────────────┐
│ Response + JSONL trace                        │
│ • sources and exact chunk IDs                 │
│ • retrieval configuration                     │
│ • provider/model and estimated token use      │
│ • verifier outcome and latency                │
└───────────────────────────────────────────────┘
```

## Data path

```text
8-source verified manifest
        │
        ▼
PMC HTML section extraction
        │
        ▼
180-word chunks / 35-word overlap
        │
        ▼
434-chunk versioned JSONL snapshot
        ├──────────────► FAISS in-memory index
        └──────────────► BM25 in-memory index
```

The legacy `learning_corpus.csv` contains 23 curated learning resources. It is
used by the portal content and retained for project history; it is not loaded into
the current answer retriever.

## Evaluation path

```text
20 approved semantic seeds
        │
        ├─ 12 answerable with source/chunk/reference claims
        ├─  3 insufficient-evidence
        ├─  4 high-risk abstention
        └─  1 prompt injection
        │
        ▼
120 deterministic paraphrase variants
        │
        ├─ offline retrieval/routing/citation/latency metrics
        └─ canonical 12-case actual-context RAGAS
```

The selected settings came from controlled chunking, embedding, retrieval/top-k,
and LLM ablations. See
[Ablation Results](../reports/Ablation_Results_2026-09-16.md).

## Proposed AWS production mapping (not yet deployed)

| Prototype component | Possible AWS component | Reason |
|---|---|---|
| JSONL evidence snapshot | Amazon S3 with versioning | Durable evidence and evaluation lineage |
| Local ingestion script | EventBridge + Step Functions/Lambda or ECS task | Scheduled, observable, retryable pipeline |
| In-memory FAISS/BM25 | OpenSearch Serverless or Aurora PostgreSQL/pgvector | Shared, scalable retrieval state |
| Streamlit/backend process | CloudFront + API Gateway + Lambda or ECS Fargate | Separate UI and stateless query service |
| External LLM gateway | Amazon Bedrock or controlled provider adapter | IAM, model routing, centralized policy |
| In-process cache | ElastiCache | Shared low-latency cache with TTL |
| JSONL trace | CloudWatch Logs/X-Ray, export to S3 | Searchable telemetry and retention |
| `.env` secrets | Secrets Manager | Rotation and least-privilege access |

This table is a design proposal. The repository proves local RAG behavior and
evaluation; it does not claim an AWS deployment.
