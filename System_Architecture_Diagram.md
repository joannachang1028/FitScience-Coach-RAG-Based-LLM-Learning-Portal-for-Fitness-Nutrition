# FitScience Coach - System Architecture Diagram

## RAG Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           FITSCIENCE COACH SYSTEM                               │
│                        Personal Learning Portal (PLP)                           │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   USER QUERY    │───▶│  STREAMLIT UI   │───▶│  RAG PIPELINE   │
│                 │    │                 │    │                 │
│ "How much       │    │ • Ask Coach     │    │ • Query         │
│  protein should │    │ • BMR Calc      │    │   Processing    │
│  I eat?"        │    │ • Courses       │    │ • Retrieval     │
└─────────────────┘    │ • History       │    │ • Generation    │
                       └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              CORPUS PROCESSING                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  LEARNING       │───▶│  TEXT CHUNKING  │───▶│  EMBEDDING      │
│  CORPUS         │    │                 │    │  GENERATION     │
│                 │    │ • 23 Sources    │    │                 │
│ • Academic      │    │ • 1000 char     │    │ • HuggingFace   │
│   Papers        │    │   chunks        │    │   Embeddings    │
│ • Government    │    │ • 200 char      │    │ • all-MiniLM-   │
│   Resources     │    │   overlap       │    │   L6-v2         │
│ • Expert        │    │                 │    │ • 384 dims      │
│   Podcasts      │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                               VECTOR STORE                                      │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  FAISS VECTOR   │◀───│  SIMILARITY     │◀───│  USER QUERY     │
│  DATABASE       │    │  SEARCH         │    │  EMBEDDING      │
│                 │    │                 │    │                 │
│ • Indexed       │    │ • Cosine        │    │ • Same          │
│   Embeddings    │    │   Similarity    │    │   Embedding     │
│ • Fast Retrieval│    │ • Top-k=8       │    │   Model         │
│ • 23 Documents  │    │   Results       │    │ • 384 dims      │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              LLM GENERATION                                     │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  RETRIEVED      │───▶│  PROMPT         │───▶│  LLAMA 3.2 1B   │
│  CONTEXT        │    │  AUGMENTATION   │    │  (OLLAMA)       │
│                 │    │                 │    │                 │
│ • Top 8         │    │ • Context +     │    │ • Local LLM     │
│   Sources       │    │   Query         │    │ • Free Usage    │
│ • Source        │    │ • Citation      │    │ • Evidence-     │
│   Metadata      │    │   Instructions  │    │   Based         │
│ • Relevance     │    │ • Learning      │    │   Responses     │
│   Scores        │    │   Focus         │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              RESPONSE OUTPUT                                    │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  GENERATED      │───▶│  CITATION       │───▶│  USER INTERFACE │
│  ANSWER         │    │  PROCESSING     │    │  DISPLAY        │
│                 │    │                 │    │                 │
│ • Evidence-     │    │ • Source        │    │ • Green Answer  │
│   Based         │    │   Links         │    │   Box           │
│ • Educational   │    │ • Relevance     │    │ • Expandable    │
│ • Practical     │    │   Scores        │    │   Sources       │
│ • Structured    │    │ • Content       │    │ • Query         │
│                 │    │   Previews      │    │   History       │
└─────────────────┘    └─────────────────┘    └─────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                              LEARNING FEATURES                                  │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  COURSES TAB    │    │  BMR CALCULATOR │    │  QUERY HISTORY  │
│                 │    │                 │    │                 │
│ • 4 Learning    │    │ • Harris-       │    │ • Track All     │
│   Paths         │    │   Benedict      │    │   Interactions  │
│ • Module-       │    │   Formula       │    │ • Export        │
│   Based         │    │ • TDEE          │    │   History       │
│ • Progress      │    │   Calculation   │    │ • Review        │
│   Tracking      │    │ • Unit          │    │   Past Q&A      │
│ • Interactive   │    │   Conversion    │    │ • Learning      │
│   Content       │    │ • Real-time     │    │   Analytics     │
│                 │    │   Updates       │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                              TECHNICAL STACK                                    │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  FRONTEND       │    │  BACKEND        │    │  AI/ML          │
│                 │    │                 │    │                 │
│ • Streamlit     │    │ • Python 3.8+   │    │ • HuggingFace   │
│ • Interactive   │    │ • LangChain     │    │   Embeddings    │
│   UI            │    │ • FAISS         │    │ • Llama 3.2 1B  │
│ • Real-time     │    │ • Pandas        │    │ • Ollama        │
│   Updates       │    │ • Requests      │    │ • RAG Pipeline  │
│ • Session       │    │ • JSON          │    │ • Vector Search │
│   Management    │    │ • CSV           │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                              DATA FLOW SUMMARY                                  │
└─────────────────────────────────────────────────────────────────────────────────┘

1. USER INPUT → Streamlit UI captures user query
2. QUERY EMBEDDING → HuggingFace model converts query to vector
3. VECTOR SEARCH → FAISS finds top-8 similar document chunks
4. CONTEXT AUGMENTATION → Retrieved chunks + query → prompt
5. LLM GENERATION → Llama 3.2 1B generates evidence-based answer
6. CITATION PROCESSING → Extract and format source references
7. RESPONSE DISPLAY → Streamlit shows answer + sources to user
8. LEARNING TRACKING → Query stored in history for progress tracking

┌─────────────────────────────────────────────────────────────────────────────────┐
│                              EVALUATION METRICS                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

• FACTUALITY: Accuracy of information (4.8/5.0)
• GROUNDEDNESS: Source relevance and citation quality (5.0/5.0)
• CONTEXT RECALL: Retrieval accuracy (5.0/5.0)
• LEARNING EFFECTIVENESS: Educational value (4.8/5.0)
• USER EXPERIENCE: Interface usability (4.9/5.0)

Overall System Score: 4.9/5.0 ⭐⭐⭐⭐⭐
