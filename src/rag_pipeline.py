"""FitScience Coach v2: evidence-grounded, traceable RAG for health education.

The LLM only summarizes retrieved evidence. Deterministic code performs
calculations, while safety policy decides when the assistant must abstain.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import time
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

from dotenv import load_dotenv
from langchain.schema import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

try:
    from langchain_openai import ChatOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from langchain_groq import ChatGroq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

try:
    from sentence_transformers import CrossEncoder
    CROSS_ENCODER_AVAILABLE = True
except ImportError:
    CROSS_ENCODER_AVAILABLE = False

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
EVIDENCE_PATH = ROOT / "data" / "evidence_corpus.jsonl"
TRACE_PATH = ROOT / "logs" / "rag_traces.jsonl"
PROMPT_VERSION = "evidence-contract-v2"
STOP_WORDS = {
    "a", "an", "the", "and", "or", "for", "to", "of", "in", "on", "is", "are",
    "i", "me", "my", "you", "your", "what", "how", "should", "can", "could", "do",
    "does", "with", "about", "from", "it", "this", "that", "be", "as", "at", "per",
}
HIGH_RISK_TERMS = {
    "pregnant", "pregnancy", "breastfeeding", "eating disorder", "anorexia", "bulimia",
    "diabetes", "kidney disease", "heart disease", "cancer", "medication", "prescription",
    "injury", "injured", "pain", "chest pain", "suicidal", "minor", "under 18",
}
PROMPT_INJECTION_TERMS = {
    "ignore previous instructions", "ignore all instructions", "reveal your system prompt",
    "show system prompt", "developer message", "jailbreak",
}
# The manifest defines what this snapshot can teach. A term occurring incidentally
# in a paper's bibliography is not enough to claim the corpus covers that topic.
COVERAGE_TERMS = {
    "protein", "resistance", "strength", "hypertrophy", "muscle", "training",
    "progression", "overload", "periodization", "sets", "repetitions",
    "body", "composition", "energy", "calorie", "calories", "neat", "activity",
    "micronutrient", "micronutrients", "vitamin", "vitamins", "mineral", "minerals",
    "supplement", "supplements", "nutrition", "nutrient", "timing", "diet",
}


def tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    for word in re.findall(r"[a-zA-Z][a-zA-Z0-9-]{1,}", text.lower()):
        tokens.append(word)
        # Keep the compound for exact matching and its parts for coverage/BM25.
        if "-" in word:
            tokens.extend(part for part in word.split("-") if len(part) > 1)
    return [word for word in tokens if word not in STOP_WORDS]


def mask_pii(text: str) -> str:
    text = re.sub(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b", "[EMAIL]", text)
    return re.sub(r"\b(?:\+?\d[\d .()-]{7,}\d)\b", "[PHONE]", text)


class FitScienceRAG:
    """Local-index RAG with hybrid retrieval, citations, safety, and traces."""

    def __init__(
        self,
        use_groq: bool = True,
        openai_api_key: Optional[str] = None,
        groq_api_key: Optional[str] = None,
        enable_reranker: bool = False,
        reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
    ) -> None:
        self.use_groq = use_groq
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY", "")
        self.groq_api_key = groq_api_key or os.getenv("GROQ_API_KEY", "")
        self.enable_reranker = enable_reranker
        self.reranker_model = reranker_model
        self.reranker = None
        self.reranker_status = "disabled"
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2", model_kwargs={"device": "cpu"})
        self.vectorstore: Optional[FAISS] = None
        self.documents: list[Document] = []
        self.doc_by_id: dict[str, Document] = {}
        self.bm25_idf: dict[str, float] = {}
        self.doc_term_counts: dict[str, Counter] = {}
        self.average_doc_length = 1.0
        self.llm: Optional[str] = None
        self.openai_llm = None
        self.groq_llm = None
        self.last_generation_model = "corpus-only"
        self.exact_cache: dict[str, dict[str, Any]] = {}

    # ------------------------------- ingestion --------------------------------
    def load_evidence_corpus(self, corpus_path: Path = EVIDENCE_PATH) -> list[Document]:
        if not corpus_path.exists():
            raise FileNotFoundError(f"Evidence snapshot not found at {corpus_path}. Run `python src/ingest_evidence.py`.")
        docs: list[Document] = []
        for line in corpus_path.read_text().splitlines():
            record = json.loads(line)
            metadata = {key: value for key, value in record.items() if key != "content"}
            metadata["source"] = record["title"]  # keeps the existing Streamlit UI compatible
            docs.append(Document(page_content=record["content"], metadata=metadata))
        if not docs:
            raise ValueError("Evidence snapshot contains no chunks")
        self.documents, self.doc_by_id = docs, {doc.metadata["chunk_id"]: doc for doc in docs}
        return docs

    def _build_bm25_index(self) -> None:
        frequency: Counter = Counter()
        total_length = 0
        self.doc_term_counts = {}
        for doc in self.documents:
            counts = Counter(tokenize(doc.page_content))
            self.doc_term_counts[doc.metadata["chunk_id"]] = counts
            frequency.update(counts.keys())
            total_length += sum(counts.values())
        self.average_doc_length = total_length / max(len(self.documents), 1)
        n_docs = len(self.documents)
        self.bm25_idf = {
            term: math.log(1 + (n_docs - count + 0.5) / (count + 0.5))
            for term, count in frequency.items()
        }

    def build_vectorstore(self, documents: Optional[list[Document]] = None) -> bool:
        documents = documents or self.documents
        if not documents:
            return False
        self.vectorstore = FAISS.from_documents(documents, self.embeddings)
        self._build_bm25_index()
        return True

    def _setup_models(self) -> None:
        if self.openai_api_key and OPENAI_AVAILABLE:
            self.llm = "openai"
        elif self.use_groq and self.groq_api_key and GROQ_AVAILABLE:
            self.llm = "groq"
        if self.enable_reranker and CROSS_ENCODER_AVAILABLE:
            try:
                self.reranker = CrossEncoder(self.reranker_model)
                self.reranker_status = f"enabled:{self.reranker_model}"
            except Exception as exc:
                self.reranker_status = f"fallback_rrf:{type(exc).__name__}"
        elif self.enable_reranker:
            self.reranker_status = "fallback_rrf:sentence-transformers-unavailable"

    def initialize_system(self) -> bool:
        try:
            self.load_evidence_corpus()
            self.build_vectorstore()
            self._setup_models()
            return True
        except Exception as exc:
            print(f"FitScience initialization failed: {exc}")
            return False

    # ------------------------------ guardrails --------------------------------
    def classify_query_risk(self, question: str) -> tuple[str, str]:
        normalized = question.lower()
        if any(term in normalized for term in PROMPT_INJECTION_TERMS):
            return "blocked", "prompt_injection"
        if any(term in normalized for term in HIGH_RISK_TERMS):
            return "high", "medical_or_vulnerable_population"
        return "standard", "education"

    @staticmethod
    def has_declared_coverage(question: str) -> bool:
        """Reject topics outside the curated manifest before fuzzy retrieval."""
        return bool(set(tokenize(question)) & COVERAGE_TERMS)

    @staticmethod
    def _safety_response(reason: str) -> str:
        if reason == "prompt_injection":
            return "I can help with evidence-based fitness and nutrition education, but I cannot follow instructions that attempt to override this safety policy."
        return ("This involves health circumstances that need individualized assessment. I can share general education from the evidence base, "
                "but please consult a qualified clinician, registered dietitian, or sports-medicine professional before changing training, diet, or supplements.")

    # ------------------------------- retrieval ---------------------------------
    def rewrite_query(self, question: str, conversation_history: Optional[Sequence[dict[str, str]]] = None) -> str:
        """Resolve short follow-ups without adding facts or calling a second model."""
        cleaned = " ".join(question.split())
        if not conversation_history or len(tokenize(cleaned)) > 4:
            return cleaned
        prior = conversation_history[-1].get("question", "")
        return f"{prior} Follow-up: {cleaned}" if prior else cleaned

    def _bm25_search(self, question: str, limit: int) -> list[tuple[str, float]]:
        scores: list[tuple[str, float]] = []
        for doc_id, counts in self.doc_term_counts.items():
            doc_length, score = sum(counts.values()), 0.0
            for term in tokenize(question):
                tf = counts.get(term, 0)
                if tf:
                    score += self.bm25_idf.get(term, 0) * (tf * 2.2) / (tf + 1.2 * (0.25 + 0.75 * doc_length / self.average_doc_length))
            if score:
                scores.append((doc_id, score))
        return sorted(scores, key=lambda item: item[1], reverse=True)[:limit]

    def _dense_search(self, question: str, limit: int) -> list[tuple[str, float]]:
        if not self.vectorstore:
            return []
        return [(doc.metadata["chunk_id"], 1 / (1 + float(distance)))
                for doc, distance in self.vectorstore.similarity_search_with_score(question, k=limit)]

    @staticmethod
    def _rrf(rankings: Sequence[Sequence[tuple[str, float]]], k: int = 60) -> dict[str, float]:
        fused: defaultdict[str, float] = defaultdict(float)
        for ranking in rankings:
            for rank, (doc_id, _) in enumerate(ranking, start=1):
                fused[doc_id] += 1 / (k + rank)
        return dict(fused)

    def _metadata_match(self, doc: Document, query_terms: set[str]) -> bool:
        return bool(query_terms & set(tokenize(" ".join(doc.metadata.get("topics", [])))))

    def retrieve(self, question: str) -> tuple[list[Document], dict[str, Any]]:
        if not self.vectorstore:
            raise RuntimeError("RAG system is not initialized")
        lexical, dense = self._bm25_search(question, 16), self._dense_search(question, 16)
        fused, query_terms = self._rrf([lexical, dense]), set(tokenize(question))
        ordered_ids = sorted(fused, key=lambda doc_id: (self._metadata_match(self.doc_by_id[doc_id], query_terms), fused[doc_id]), reverse=True)
        candidates = [self.doc_by_id[doc_id] for doc_id in ordered_ids[:16]]
        scores = {doc_id: fused[doc_id] for doc_id in ordered_ids}
        if self.reranker and candidates:
            rerank_scores = self.reranker.predict([(question, doc.page_content) for doc in candidates])
            ranked = sorted(zip(rerank_scores, candidates), key=lambda pair: pair[0], reverse=True)
            candidates, scores = [doc for _, doc in ranked], {doc.metadata["chunk_id"]: float(score) for score, doc in ranked}
        lexical_terms_found = len(set(term for doc_id, _ in lexical for term in self.doc_term_counts[doc_id]) & query_terms)
        if lexical_terms_found == 0:
            return [], {"reason": "no_lexical_evidence", "candidate_count": len(candidates)}
        selected = candidates[:4]
        if len(candidates) > 4 and scores.get(candidates[0].metadata["chunk_id"], 0) > scores.get(candidates[3].metadata["chunk_id"], 0) * 1.35:
            selected = candidates[:2]
        return selected, {
            "reason": "retrieved", "candidate_count": len(candidates), "selected_count": len(selected),
            "lexical_terms_found": lexical_terms_found, "reranker": self.reranker_status,
            "dense_candidates": [{"chunk_id": item, "score": round(score, 4)} for item, score in dense[:5]],
            "lexical_candidates": [{"chunk_id": item, "score": round(score, 4)} for item, score in lexical[:5]],
        }

    # --------------------------- generation + citations -----------------------
    def _build_context(self, docs: Sequence[Document]) -> tuple[str, dict[str, Document]]:
        labels: dict[str, Document] = {}
        blocks: list[str] = []
        for index, doc in enumerate(docs, start=1):
            label, meta = f"S{index}", doc.metadata
            labels[label] = doc
            blocks.append(f"[{label}] {meta['title']} | section: {meta.get('section', 'Unknown')} | DOI: {meta.get('doi', 'not listed')}\n{doc.page_content}")
        return "\n\n".join(blocks), labels

    def _get_model(self, provider: str):
        if provider == "openai":
            if not self.openai_llm:
                self.openai_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=self.openai_api_key)
            return self.openai_llm
        if provider == "groq":
            if not self.groq_llm:
                self.groq_llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0, api_key=self.groq_api_key)
            return self.groq_llm
        return None

    def _generate(self, question: str, context: str) -> str:
        prompt = f"""You are FitScience Coach, an educational fitness and nutrition assistant.
Use only the evidence excerpts below. Do not diagnose, prescribe, infer missing facts, or add general knowledge.

Answer contract:
- Give 1-4 concise factual bullet points.
- Every bullet must end with source labels exactly like [S1].
- Use a label only when its excerpt explicitly supports that bullet.
- If evidence does not answer the question, say: "The available evidence snapshot does not answer this question."
- Do not include a references section.

Evidence excerpts:
{context}

Question: {question}
Answer:"""
        # Model gateway policy: primary OpenAI generation, then Groq only on a
        # provider failure. The route is recorded in the trace for cost/quality analysis.
        routes = []
        if self.openai_api_key and OPENAI_AVAILABLE:
            routes.append("openai")
        if self.use_groq and self.groq_api_key and GROQ_AVAILABLE:
            routes.append("groq")
        self.last_generation_model = "corpus-only"
        for provider in routes:
            try:
                response = self._get_model(provider).invoke(prompt)
                self.last_generation_model = provider
                return response.content.strip() if hasattr(response, "content") else str(response)
            except Exception as exc:
                print(f"{provider} generation failed; trying configured fallback: {type(exc).__name__}")
        return ""

    @staticmethod
    def _fallback_answer(docs: Sequence[Document], question: str = "") -> str:
        """Extract the most query-supported sentence when no generator is configured."""
        query_terms = set(tokenize(question))
        bullets, used_sources = [], set()
        for index, doc in enumerate(docs, start=1):
            source_id = doc.metadata.get("source_id")
            if source_id in used_sources:
                continue
            sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", doc.page_content) if sentence.strip()]
            if not sentences:
                continue
            sentence = max(
                sentences,
                key=lambda item: (len(query_terms & set(tokenize(item))), min(len(item.split()), 45)),
            )
            # Avoid displaying an arbitrary sentence when no words support it.
            if query_terms and not (query_terms & set(tokenize(sentence))):
                continue
            bullets.append(f"- {sentence} [S{index}]")
            used_sources.add(source_id)
            if len(bullets) == 2:
                break
        return "\n".join(bullets) if bullets else "The available evidence snapshot does not answer this question."

    def verify_answer_contract(self, answer: str, labels: dict[str, Document], question: str = "") -> tuple[str, dict[str, Any]]:
        valid, rejected = [], []
        for raw_line in answer.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            citations = re.findall(r"\[(S\d+)\]", line)
            if not citations or any(citation not in labels for citation in citations):
                rejected.append(line)
                continue
            claim_terms = set(tokenize(re.sub(r"\[S\d+\]", "", line)))
            evidence_terms = set().union(*(set(tokenize(labels[citation].page_content)) for citation in citations))
            if len(claim_terms & evidence_terms) < 2:
                rejected.append(line)
                continue
            valid.append(line if line.startswith("-") else f"- {line}")
        if not valid:
            return self._fallback_answer(list(labels.values()), question), {"status": "fallback", "rejected_claims": rejected}
        return "\n".join(valid), {"status": "passed", "rejected_claims": rejected}

    # ---------------------------- observability/cache -------------------------
    @staticmethod
    def _cache_key(question: str) -> str:
        return hashlib.sha256(question.strip().lower().encode()).hexdigest()

    @staticmethod
    def _write_trace(event: dict[str, Any]) -> None:
        TRACE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with TRACE_PATH.open("a") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")

    @staticmethod
    def _source_payload(doc: Document, index: int) -> dict[str, Any]:
        meta = doc.metadata
        return {
            "label": f"S{index}", "chunk_id": meta["chunk_id"], "source_id": meta["source_id"],
            "title": meta["title"], "url": meta["url"], "doi": meta.get("doi", ""),
            "section": meta.get("section", ""), "published_year": meta.get("published_year"),
            "evidence_level": meta.get("evidence_level", ""), "population": meta.get("population", ""),
            "content_preview": doc.page_content[:280] + "…",
        }

    def query(self, question: str, conversation_history: Optional[Sequence[dict[str, str]]] = None) -> Dict[str, Any]:
        start, trace_id = time.perf_counter(), uuid.uuid4().hex
        safe_question = mask_pii(question.strip())
        risk, reason = self.classify_query_risk(safe_question)
        event: dict[str, Any] = {
            "trace_id": trace_id, "timestamp": datetime.now(timezone.utc).isoformat(), "query": safe_question,
            "prompt_version": PROMPT_VERSION, "model": self.llm or "corpus-only", "risk": risk, "risk_reason": reason,
        }
        if risk in {"blocked", "high"}:
            event.update({"outcome": "abstained", "latency_ms": round((time.perf_counter() - start) * 1000, 1)})
            self._write_trace(event)
            return {"answer": self._safety_response(reason), "sources": [], "trace_id": trace_id, "status": "abstained"}
        if not self.has_declared_coverage(safe_question):
            event.update({"outcome": "insufficient_evidence", "coverage": "out_of_manifest",
                          "latency_ms": round((time.perf_counter() - start) * 1000, 1)})
            self._write_trace(event)
            return {"answer": "This question is outside the topics covered by the current evidence snapshot, so I cannot answer it safely.",
                    "sources": [], "trace_id": trace_id, "status": "insufficient_evidence", "cache_hit": False}
        rewritten, cache_key = self.rewrite_query(safe_question, conversation_history), self._cache_key(safe_question)
        if cache_key in self.exact_cache:
            cached = dict(self.exact_cache[cache_key])
            cached.update({"trace_id": trace_id, "cache_hit": True})
            event.update({"outcome": "cache_hit", "latency_ms": round((time.perf_counter() - start) * 1000, 1)})
            self._write_trace(event)
            return cached
        try:
            docs, retrieval = self.retrieve(rewritten)
            event.update({"rewritten_query": rewritten, "retrieval": retrieval})
            if not docs:
                result = {"answer": "I do not have sufficiently relevant evidence in this snapshot to answer that safely. Please try a more specific fitness or nutrition education question.",
                          "sources": [], "trace_id": trace_id, "status": "insufficient_evidence", "cache_hit": False}
            else:
                context, labels = self._build_context(docs)
                answer, verification = self.verify_answer_contract(
                    self._generate(rewritten, context) or self._fallback_answer(docs, rewritten),
                    labels,
                    rewritten,
                )
                result = {"answer": answer, "sources": [self._source_payload(doc, i) for i, doc in enumerate(docs, 1)],
                          "trace_id": trace_id, "status": "answered", "citation_verifier": verification, "cache_hit": False}
                event["citation_verifier"] = verification
                event["generation_model"] = self.last_generation_model
            self.exact_cache[cache_key] = dict(result)
            event.update({"outcome": result["status"], "retrieved_chunk_ids": [doc.metadata["chunk_id"] for doc in docs],
                          "latency_ms": round((time.perf_counter() - start) * 1000, 1)})
            self._write_trace(event)
            return result
        except Exception as exc:
            event.update({"outcome": "error", "error": type(exc).__name__, "latency_ms": round((time.perf_counter() - start) * 1000, 1)})
            self._write_trace(event)
            return {"error": f"Query failed: {exc}", "trace_id": trace_id}

    # Deterministic calculation tools remain outside LLM generation.
    @staticmethod
    def calculate_bmr(weight_kg: float, height_cm: float, age: int, gender: str) -> float:
        if gender.lower() in {"male", "m", "man"}:
            return round(88.362 + 13.397 * weight_kg + 4.799 * height_cm - 5.677 * age, 1)
        if gender.lower() in {"female", "f", "woman"}:
            return round(447.593 + 9.247 * weight_kg + 3.098 * height_cm - 4.330 * age, 1)
        raise ValueError("Gender must be 'male' or 'female'")

    @staticmethod
    def calculate_tdee(bmr: float, activity_level: str) -> float:
        multipliers = {"sedentary": 1.2, "lightly_active": 1.375, "moderately_active": 1.55, "very_active": 1.725, "extremely_active": 1.9}
        if activity_level.lower() not in multipliers:
            raise ValueError(f"Invalid activity level. Choose from: {list(multipliers)}")
        return round(bmr * multipliers[activity_level.lower()], 1)
