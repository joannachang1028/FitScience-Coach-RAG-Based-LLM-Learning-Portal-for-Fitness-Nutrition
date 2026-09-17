# FitScience Coach — AWS Solutions Architect Interview Q&A

The answers below distinguish what the prototype actually implements from how it
could be productionized on AWS. Do not say the project runs on AWS unless you have
deployed it there.

## 1. Explain your RAG project. How did you evaluate it and decide what to improve?

> I built FitScience Coach, an evidence-grounded fitness and nutrition education
> assistant. The current retrieval path indexes 434 provenance-preserving chunks
> from eight verified open-access sources. It combines a 384-dimensional MiniLM
> embedding in FAISS with BM25 lexical retrieval, fuses both rankings, retrieves
> six chunks, and asks GPT-4.1-mini to produce citation-bound claims.
>
> My main engineering change was separating failure domains. I measure whether
> routing made the right answer-or-abstain decision, whether retrieval found the
> expected article and exact evidence, and whether generation remained faithful
> and relevant. I use 20 reviewed semantic seeds expanded into 120 regression
> variants. Retrieval changes are selected with deterministic metrics first; I run
> RAGAS only after a meaningful system boundary, such as the baseline, selected
> retriever, or model comparison.
>
> The selected retrieval policy reached expected-source recall of 1.0, but strict
> gold-chunk recall was 0.27 and answer relevance was 0.593. That tells me the next
> bottleneck is precise evidence selection and evaluation breadth, not simply
> choosing a larger foundation model.

## 2. What does the old 0.857 score mean?

> It is a historical five-example RAGAS aggregate from the prototype. The old
> evaluator supplied prewritten contexts instead of the chunks retrieved at run
> time, so it cannot prove retrieval quality. I would not call it 85.7 percent
> accuracy or clinical correctness. I retained it for project history and replaced
> it with actual-context retrieval and generation metrics.

## 3. Why hybrid retrieval instead of dense search alone?

> Dense retrieval helps when the query and evidence express the same concept with
> different words. BM25 is strong when exact terms, acronyms, dosage units, or
> clinical vocabulary matter. I tested them rather than assuming hybrid was
> better. Dense top-4 produced evidence F1 of 0.185, BM25 top-4 produced 0.208,
> and hybrid top-4 produced 0.216. Hybrid top-6 reached 0.232 and full expected-
> source recall. The cost is a larger prompt, not meaningful local retrieval
> latency.

## 4. How did you choose chunk size?

> I reconstructed the same immutable source sections and compared 100 words with
> 20-word overlap, 180/35, and 300/50. Small chunks increased evidence precision
> but source recall fell to 0.889. Large chunks raised evidence recall but added
> irrelevant text. The 180/35 middle option had the best evidence F1, source
> recall, and latency balance. I also added a chunk-boundary-independent trigram
> metric because exact chunk IDs are not comparable after re-chunking.

## 5. Why top-6, and what is the trade-off?

> Adaptive top-2-to-4 used about 536 context words and achieved evidence F1 of
> 0.214. Fixed top-6 used about 915 words, improved F1 to 0.232, gold-chunk recall
> from 0.163 to 0.270, and source recall from 0.986 to 1.0. Local p95 stayed under
> 7 milliseconds, so retrieval compute was not the issue. The trade-off is about
> 71 percent more prompt context, which affects model cost and can reduce answer
> focus. I chose recall for this health-evidence use case and then re-ran RAGAS to
> check the generation impact.

## 6. Why GPT-4.1-mini instead of GPT-4o-mini?

> On the same 12 answerable cases and retrieved contexts, both had RAGAS
> faithfulness of 1.0 and context recall of 0.944. GPT-4.1-mini improved answer
> relevance from 0.522 to 0.593 and citation-contract compliance from 0.917 to
> 1.0. Its p50 latency was about 1.36 seconds versus 1.09 seconds, and its list
> token price was about 2.67 times higher. I use it as the quality default but
> would keep GPT-4o-mini as a cost-sensitive route. With only 12 judged examples,
> I describe this as a candidate decision, not a statistically proven win.

## 7. How do you prevent hallucinations and unsafe health advice?

> I use several independent controls. Before retrieval, the app masks common PII,
> detects prompt-injection phrases, routes high-risk medical or vulnerable-
> population questions to abstention, and checks whether the topic is in the
> evidence manifest. The prompt permits only retrieved evidence. After generation,
> every bullet must end with a valid source label and pass a lexical support check;
> unsupported lines are removed. If generation fails, the system uses a retrieved
> source sentence rather than free-form model knowledge.

## 8. RAG or fine-tuning?

> I would use RAG for changing, attributable knowledge because sources can be
> updated, filtered, and cited without retraining. Fine-tuning is better for stable
> behavior—format, tone, classification, or task execution—when we have a suitable
> dataset. It does not automatically teach the model current evidence or provide
> provenance. In this project the measured weakness is evidence selection and
> answer relevance, so I would not fine-tune until retrieval and human-reviewed
> labels are stronger. They can later be combined: RAG for facts, fine-tuning for
> behavior.

## 9. Why did you not add agentic RAG?

> I use complexity only when a test demonstrates the need. The selected single-hop
> retriever reached source recall of 1.0 and RAGAS context recall of 0.944. The
> current approved set has no multi-hop cases proving that query decomposition or
> iterative tools would help. An agent would add latency, cost, state management,
> permissions, and a larger failure surface. I would first add reviewed multi-
> document and ambiguous follow-up cases, then compare deterministic rewriting,
> multi-query retrieval, and only then agentic planning.

## 10. How would you deploy this on AWS?

> The current prototype is local Streamlit, FAISS, and JSONL; I would present AWS
> as a target design, not completed work. I would put versioned evidence and
> evaluation artifacts in S3, run ingestion as an event-driven or scheduled job,
> expose the query service behind API Gateway and Lambda or ECS Fargate depending
> on cold-start and model-index memory requirements, and use a managed vector
> store such as OpenSearch Serverless or Aurora PostgreSQL with pgvector. For model
> access, Amazon Bedrock would reduce provider integration and IAM surface, while
> a customer-managed knowledge base would preserve control over chunking and
> retrieval experiments.
>
> I would keep deterministic safety routing in the application layer, store
> secrets in Secrets Manager, encrypt S3 and the vector store with KMS, apply
> least-privilege IAM, and send metrics, structured logs, and traces to CloudWatch.
> AWS documentation explicitly treats lineage, versioning, data quality, security,
> and low-latency retrieval as core RAG data-architecture concerns, and Bedrock
> Knowledge Bases supports managed or customer-managed vector stores and citations.

AWS references: [Generative AI Lens — data architecture](https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/data-architecture.html),
[Bedrock Knowledge Bases](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html).

## 11. How would you make it highly available and control cost?

> I would separate the stateless query API from ingestion and indexing. The API can
> scale horizontally across Availability Zones; the managed data stores provide
> durable shared state. I would set timeouts and circuit breakers around model
> providers, return an explicit evidence-only fallback, and use idempotent ingestion
> jobs with versioned indexes so rollback is a pointer change rather than an in-
> place rebuild.
>
> For cost, I would route simple classification and rewriting to smaller models,
> cache stable non-personalized answers, batch embedding jobs, cap retrieved tokens,
> and compare quality per dollar rather than model quality alone. The project gives
> a concrete example: top-6 improved recall but increased context words by 71%, and
> GPT-4.1-mini improved relevance but cost about 2.67 times GPT-4o-mini per token.

## 12. What would you monitor in production?

> I would monitor each stage separately: routing distribution and false abstentions;
> retrieval empty rate, source recall proxies, score distributions, and context
> size; model latency, token use, provider errors, and fallback rate; citation-
> contract failures; user feedback; and end-to-end p50, p95, cost, and error rate.
> Every request needs a correlation ID and versioned source snapshot, embedding,
> retrieval configuration, prompt, and model so I can reproduce an answer.
>
> I would mask sensitive data before logging and limit trace access. AWS's
> Generative AI Lens recommends prompt/model/asset traceability and end-to-end RAG
> tracing, while warning that traces themselves may contain sensitive data.

AWS reference: [Enable tracing for agents and RAG workflows](https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/genops03-bp02.html).

## 13. Tell me about a failure you found and how you handled it.

> The source audit found two PMC IDs whose actual articles did not match the
> manifest descriptions. I disabled those sources, corrected four DOI records, and
> remapped only labels supported by existing valid sources. I did not silently
> preserve the corpus size. Later, the Groq fallback model ID returned NotFound and
> its replacement hit a rate limit during evaluation. I excluded corpus-only
> fallback outputs from the model comparison and documented the fallback as not
> quality-approved. Those examples show why provenance and provider identity must
> be part of every trace.

## 14. What would you improve next?

> First, expand and domain-review the evaluation set, especially the ketogenic-
> diet coverage false positive, multilingual queries, multi-document questions,
> and adversarial citation cases. Second, repeat the LLM comparison to quantify
> variance and establish confidence intervals. Third, improve evidence ranking—
> possibly a reranker—only if it beats the fixed top-6 baseline on the same labels
> and justifies its latency. I would not add more sources, fine-tuning, or an agent
> without a defined failure and acceptance metric.
