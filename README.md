# FitScience Coach - Personal Learning Portal

An evidence-based fitness and nutrition learning portal powered by RAG (Retrieval-Augmented Generation) technology.

## 🎯 Project Overview

**FitScience Coach** helps users learn evidence-based fitness and nutrition through:
- Interactive Q&A with citations
- Curated learning corpus from academic papers, guidelines, and expert podcasts
- Progress tracking and personalized recommendations
- Modular learning paths covering training, nutrition, and health

## 📚 Learning Objectives

1. **Design** a weekly training plan with progression, rest, and goal alignment
2. **Synthesize** nutrition targets (protein, carbs, fat, calories) with training goals, lifestyle, and preferences  
3. **Identify** food choices to meet daily calorie and micronutrient needs (vitamins, minerals)
4. **Calculate** daily calorie consumption based on body goals (fat loss, muscle gain, maintenance) using BMR and NEAT data

## 🏗️ System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    FITSCIENCE COACH SYSTEM                      │
│              Personal Learning Portal (PLP)                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │         USER INTERFACE LAYER            │
        │         (Streamlit Web App)             │
        └─────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │           RAG PIPELINE LAYER            │
        │    (Query → Retrieve → Generate)        │
        └─────────────────────────────────────────┘
                              │
                ┌─────────────┼─────────────┐
                ▼             ▼             ▼
        ┌───────────┐  ┌───────────┐  ┌───────────┐
        │  VECTOR   │  │   LLM     │  │  CORPUS   │
        │   STORE   │  │  ENGINE   │  │   DATA    │
        │  (FAISS)  │  │(GPT/Groq) │  │ (23 src)  │
        └───────────┘  └───────────┘  └───────────┘
```

### Detailed RAG Pipeline

```
User Query
    ↓
[1] Query Processing
    ↓
[2] Embedding Generation (HuggingFace all-MiniLM-L6-v2)
    ↓
[3] Vector Similarity Search (FAISS, top-k=8)
    ↓
[4] Context Augmentation
    ↓
[5] LLM Generation (GPT-4o-mini / Groq Llama)
    ↓
[6] Citation Processing
    ↓
[7] Response Display with Sources
```

### Data Flow Diagram

```
┌──────────────┐
│   User       │
│   Input      │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────────────┐
│  Streamlit Interface                         │
│  • Ask Coach Tab                             │
│  • BMR Calculator Tab                        │
│  • Courses Tab                               │
│  • Query History Tab                         │
└──────┬───────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────┐
│  RAG Pipeline (rag_pipeline.py)              │
│  ┌────────────────────────────────────────┐  │
│  │ 1. Load Corpus (23 sources)           │  │
│  │ 2. Text Chunking (1000 chars)         │  │
│  │ 3. Generate Embeddings (384 dims)     │  │
│  │ 4. Build FAISS Index                  │  │
│  └────────────────────────────────────────┘  │
└──────┬───────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────┐
│  Vector Store (FAISS)                        │
│  • 23 document embeddings                    │
│  • Cosine similarity search                  │
│  • Fast retrieval (< 100ms)                  │
└──────┬───────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────┐
│  LLM Generation                              │
│  ┌────────────────────────────────────────┐  │
│  │ Primary: OpenAI GPT-4o-mini (optional)│  │
│  │ • Temperature: 0.0                    │  │
│  │ • Strict grounding prompt             │  │
│  │                                       │  │
│  │ Default: Groq Llama (free cloud)      │  │
│  │ • No local install                    │  │
│  │ • Free tier at console.groq.com       │  │
│  │ • Configure GROQ_API_KEY in .env      │  │
│  └────────────────────────────────────────┘  │
└──────┬───────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────┐
│  Response Processing                         │
│  • Extract citations                         │
│  • Format sources                            │
│  • Add relevance scores                      │
└──────┬───────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────┐
│  User Interface Display                      │
│  • Green answer box                          │
│  • Expandable sources                        │
│  • Query history tracking                    │
└──────────────────────────────────────────────┘
```

### Components:
- **Corpus**: 23 evidence-based sources (papers, guidelines, podcasts)
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2, 384 dimensions)
- **Vector Store**: FAISS for fast similarity search
- **LLM**: Groq Llama (default, free) — OpenAI GPT-4o-mini optional for higher faithfulness
- **Interface**: Streamlit web app with 4 interactive tabs

### Performance:
- **RAGAs Score**: 0.857 (Excellent) ⭐⭐⭐⭐⭐
- **Retrieval Metrics**: Perfect 1.0 across all dimensions
- **Faithfulness**: 0.429 (286% improvement through optimization)
- **Query Processing**: < 2 seconds average

---

## 📁 Project Structure

```
Application-of-NLX-LLM-Personal-Learning-Portal/
│
├── README.md                                  # 📄 Project overview and documentation
├── requirements.txt                           # 📦 Python dependencies
│
├── data/                                      # 📊 Data files
│   └── learning_corpus.csv                    # 23 curated sources
│
├── src/                                       # 💻 Source code
│   ├── rag_pipeline.py                        # Core RAG system implementation
│   ├── streamlit_app.py                       # Streamlit web interface
│   └── ragas_evaluation_v3.py                 # RAGAs evaluation script
│
├── diagrams/                                  # 📐 System architecture
│   └── system_architecture.md                 # Detailed architecture documentation
│
├── reports/                                   # 📑 Documentation and reports
│   ├── Final_Report.md                        # Comprehensive final report
│   ├── Evaluation_Log_and_Samples.md          # Detailed evaluation with samples
│   ├── RAG_Evaluation_and_Improvements.md     # Complete iterative improvement journey
│   │
│   ├── Domain_Learning_Goals.md               # Domain definition & learning objectives (Step 1)
│   └── PLP_Features_To_Adopt.md               # PLP feature analysis (Step 2)
│
└── ragas_results/                             # 📈 RAGAs evaluation results
    ├── ragas_evaluation_results.json          # Final evaluation score (0.857)
    ├── ragas_aggregate_results.json           # Aggregated evaluation metrics
    └── ragas_scores_per_sample.csv            # Per-sample evaluation scores
```

### Directory Organization

**📊 `data/`** - Core data files
- `learning_corpus.csv` - 23 curated sources (Academic Papers, Podcasts, Government Resources)

**💻 `src/`** - Source code (3 files)
- `rag_pipeline.py` - RAG system with Groq Llama (default) + optional OpenAI GPT-4o-mini
- `streamlit_app.py` - Interactive web interface with 4 tabs (Courses, Ask Coach, BMR Calculator, Query History)
- `ragas_evaluation_v3.py` - Automated RAGAs evaluation script

**📐 `diagrams/`** - System architecture (1 file)
- `system_architecture.md` - Comprehensive architecture documentation with data flow diagrams

**📑 `reports/`** - Documentation (5 files)
- `Final_Report.md` - Complete project report with architecture, evaluation, and reflections
- `Evaluation_Log_and_Samples.md` - RAGAs results and sample queries
- `Domain_Learning_Goals.md` - Learning domain, questions, and objectives (Step 1)
- `PLP_Features_To_Adopt.md` - Analyzed PLP features (Step 2)
- `RAG_Evaluation_and_Improvements.md` - Complete iterative improvement journey (v1.0 → v3.0)

**📈 `ragas_results/`** - Evaluation results (3 files)
- `ragas_evaluation_results.json` - Final score: 0.857 (Excellent) ⭐⭐⭐⭐⭐
- `ragas_aggregate_results.json` - Aggregated metrics across all samples
- `ragas_scores_per_sample.csv` - Detailed per-sample evaluation scores

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API Key (host only)
Create a `.env` file with your Groq API key (free at [console.groq.com](https://console.groq.com)):
```
GROQ_API_KEY=gsk_your-key-here
```
Users visiting the app do **not** need to set any API keys — it works out of the box once the host configures `.env`.

### 3. Run the Streamlit App
```bash
streamlit run src/streamlit_app.py
```

### 4. Access the Interface
Open your browser to `http://localhost:8501`

---

## 🤖 Core Features

### 1. Intelligent Q&A System
**LLM Approach**:
- **Groq Llama** (Default): Free cloud API — no OpenAI key or local install needed. Host sets `GROQ_API_KEY` in `.env`; users use the app directly.
- **OpenAI GPT-4o-mini** (Optional): Add `OPENAI_API_KEY` for higher faithfulness
- **Corpus-only mode**: Safe fallback with direct source extraction when no LLM is configured

**Key Capabilities**:
- Evidence-based answers grounded in curated research
- Automatic source citations with URLs and metadata
- Top-8 relevant document retrieval using FAISS
- Adaptive search: falls back to broader terms if no results found
- Conservative language: "According to [source]..." for transparency

### 2. BMR & TDEE Calculator
**Harris-Benedict Equation Implementation**:
- Calculate Basal Metabolic Rate (BMR) based on:
  - Weight (kg), Height (cm), Age, Gender
- Calculate Total Daily Energy Expenditure (TDEE) with activity multipliers:
  - Sedentary (1.2x)
  - Lightly Active (1.375x)
  - Moderately Active (1.55x)
  - Very Active (1.725x)
  - Extremely Active (1.9x)

### 3. Learning Corpus Management
**23 Evidence-Based Sources**:
- **Academic Papers** (9): Protein requirements, BMR calculations, training volume
- **Podcasts** (8): Expert interviews on fitness, nutrition, and health
- **Government Resources** (6): USDA MyPlate, NIH, NHS guidelines

**Content Mapping**:
- Protein requirements and supplementation
- BMR/TDEE/NEAT calculations
- Training progression and periodization
- Workout splits and program design
- Micronutrients and supplementation
- Sleep and recovery optimization

### 4. RAG Pipeline Features
**Document Processing**:
- RecursiveCharacterTextSplitter (1000 chars, 200 overlap)
- Synthetic content generation from corpus metadata
- HuggingFace embeddings (all-MiniLM-L6-v2, 384 dimensions)
- FAISS vector store for fast similarity search

**Query Processing**:
- Retrieve top-8 relevant documents
- Build context with source metadata
- Generate LLM response with strict grounding prompts
- Return answer with source links and previews

**Faithfulness Optimizations**:
- Temperature 0.0 (OpenAI / Groq) for conservative responses
- Strict prompts: "Answer ONLY using information from sources"
- Top-p 0.7, top-k 20 for focused sampling
- Explicit source attribution required
- Corpus fallback for failed LLM responses

### 5. Streamlit Web Interface
**4 Interactive Tabs**:
1. **Courses**: Module-based learning paths with progress tracking
2. **Ask Coach**: Interactive Q&A with quick question buttons
3. **BMR Calculator**: Harris-Benedict formula with unit conversion
4. **Query History**: Track all interactions and export history

**Session State Management**:
- Persistent query history
- Learning progress tracking
- Real-time UI updates

---

## 📊 Learning Corpus

The system uses a curated corpus of 23 evidence-based sources:

### Source Types:
- **Academic Papers**: Protein requirements, BMR calculations, training volume
- **Government Resources**: USDA MyPlate, NIH fact sheets, NHS programs
- **Expert Content**: Jeff Cavaliere (Athlean-X), expert podcast episodes
- **Research Reviews**: Micronutrients, NEAT, sleep and performance

### Key Domains Covered:
- ✅ Training programming and progression
- ✅ Macronutrient targets and timing
- ✅ Micronutrient needs and sources
- ✅ Calorie calculation (BMR, TDEE, NEAT)
- ✅ Sleep and recovery optimization
- ✅ Evidence-based supplementation

---

## 🔧 Technical Details

### RAG Pipeline (`src/rag_pipeline.py`)

**Core Class: `FitScienceRAG`**

```python
from src.rag_pipeline import FitScienceRAG

# Initialize — Groq from .env (no user API key needed)
rag = FitScienceRAG(
    use_groq=True,                     # Default: Groq Llama (free)
    groq_api_key="gsk_...",            # Or set GROQ_API_KEY in .env
    openai_api_key="sk-..."            # Optional: for higher faithfulness
)

# Initialize system
rag.initialize_system()

# Query the system
result = rag.query("How much protein should I eat?")

# Result structure
{
    "answer": "Evidence-based answer with citations...",
    "sources": [
        {
            "title": "Source title",
            "url": "https://...",
            "type": "Academic Paper",
            "relevance": "High",
            "notes": "Description",
            "content_preview": "Preview text..."
        }
    ]
}
```

**Key Methods**:
- `load_corpus_from_csv()`: Load 23 sources from CSV
- `create_synthetic_content()`: Generate documents with metadata mapping
- `build_vectorstore()`: Create FAISS index with HuggingFace embeddings
- `query()`: Main query interface with LLM generation
- `calculate_bmr()`: Harris-Benedict BMR calculation
- `calculate_tdee()`: TDEE with activity multipliers
- `generate_openai_response()`: GPT-4o-mini (optional, high faithfulness)
- `generate_groq_response()`: Groq Llama (default, free cloud API)

**LLM Priority System**:
1. **OpenAI GPT-4o-mini** (if `OPENAI_API_KEY` set): Best faithfulness
2. **Groq Llama** (if `GROQ_API_KEY` in .env): Free, no user setup
3. **Corpus-only fallback**: Direct source extraction

### Vector Store:
- **Embeddings**: HuggingFace sentence-transformers (all-MiniLM-L6-v2)
- **Storage**: FAISS for fast similarity search
- **Chunking**: 1000 chars with 200 overlap
- **Retrieval**: Top-8 documents with metadata

---

## 📈 Evaluation & Performance

### RAGAs Automated Evaluation

**Final Score: 0.857 / 1.0 (Excellent) ⭐⭐⭐⭐⭐**

| Metric | Score | Status |
|--------|-------|--------|
| Context Precision | 1.000 | ⭐⭐⭐⭐⭐ Perfect |
| Context Recall | 1.000 | ⭐⭐⭐⭐⭐ Perfect |
| Context Relevance | 1.000 | ⭐⭐⭐⭐⭐ Perfect |
| Faithfulness | 0.429 | ⭐⭐⭐⭐ Good |
| **Overall** | **0.857** | ⭐⭐⭐⭐⭐ **Excellent** |

### Iterative Improvement Journey

1. **v1.0** (Llama 3.2 1B): 0.779 - Good baseline, perfect retrieval
2. **v2.0** (Optimized Llama): 0.778 - Optimization attempts showed model limitations
3. **v3.0** (OpenAI GPT-4o-mini): **0.857** - 286% faithfulness improvement

**Key Learning**: Model selection is critical for faithfulness. Perfect retrieval validates corpus design.

### Run Evaluation
```bash
# Set GROQ_API_KEY and optionally OPENAI_API_KEY in .env
python src/ragas_evaluation_v3.py
```

---

## 📝 Usage Examples

### Sample Queries:
1. "How much protein should I eat for muscle building?"
2. "How do I calculate my daily calorie needs?"
3. "What is progressive overload in training?"
4. "What supplements are actually evidence-based?"
5. "How much sleep do I need for recovery?"

### Expected Output:
- Evidence-based answers with practical advice
- Source citations with links to original papers
- Relevance scores and content previews
- Structured, actionable recommendations

---

## 🎓 Assignment 3 Deliverables

| Deliverable | Location |
|-------------|----------|
| **System Code** | `src/rag_pipeline.py`, `src/streamlit_app.py` |
| **Learning Corpus** | `data/learning_corpus.csv` (23 sources) |
| **PLP Interface** | `src/streamlit_app.py` (Streamlit app) |
| **Evaluation Script** | `src/ragas_evaluation_v3.py` |
| **Evaluation Results** | `ragas_results/ragas_evaluation_results.json` (Score: 0.857) |
| **Evaluation Log** | `reports/Evaluation_Log_and_Samples.md` |
| **Final Report** | `reports/Final_Report.md` |
| **System Architecture** | `diagrams/system_architecture.md` |
| **Step Documentation** | `reports/Domain_Learning_Goals.md`, `reports/PLP_Features_To_Adopt.md` |
| **GitHub Repository** | [Ready for submission] |

---

## 🔮 Future Enhancements

### Optional Bonus Features:
- **Reasoning Agents**: Chain-of-thought reasoning for complex queries
- **Multi-Agent Workflow**: Planner → Searcher → Summarizer pipeline
- **Knowledge Graph**: Neo4j integration for concept relationships

### Additional Features:
- User profile and goal tracking
- Personalized plan generation
- Integration with fitness tracking apps
- Real document extraction (replace synthetic content)
- Fine-tuning on domain corpus

---

## 🤝 Contributing

This is an academic project for Assignment 3. For improvements:
1. Add more diverse sources to the corpus
2. Implement advanced evaluation metrics
3. Enhance the user interface
4. Add personalized recommendation features

---

## 📄 License

Academic project - see assignment guidelines for usage terms.

---

**FitScience Coach** - Making evidence-based fitness and nutrition accessible to everyone! 🏋️‍♀️💪
