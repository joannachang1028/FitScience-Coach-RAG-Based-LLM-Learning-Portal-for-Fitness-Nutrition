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

```
User Query → RAG Pipeline → Vector Search → LLM Generation → Response + Citations
```

### Components:
- **Corpus**: 23 evidence-based sources (papers, guidelines, podcasts)
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)
- **Vector Store**: FAISS for fast similarity search
- **LLM**: Hybrid approach - OpenAI GPT-4o-mini (primary) + Llama 3.2 1B (fallback)
- **Interface**: Streamlit web app

### Performance:
- **RAGAs Score**: 0.857 (Excellent) ⭐⭐⭐⭐⭐
- **Retrieval Metrics**: Perfect 1.0 across all dimensions
- **Faithfulness**: 0.429 (286% improvement through optimization)

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables (Optional)
```bash
export OPENAI_API_KEY="your-api-key-here"
```

### 3. Run the Streamlit App
```bash
streamlit run src/streamlit_app.py
```

### 4. Access the Interface
Open your browser to `http://localhost:8501`

## 📊 Learning Corpus

The system uses a curated corpus of 23 evidence-based sources:

### Source Types:
- **Academic Papers**: Protein requirements, BMR calculations, training volume
- **Guidelines**: ACSM position stands, NSCA recommendations  
- **Government Resources**: USDA MyPlate, NIH fact sheets, NHS programs
- **Expert Content**: Jeff Cavaliere (Athlean-X), Diary of a CEO podcast episodes
- **Research Reviews**: Micronutrients, NEAT, sleep and performance

### Key Domains Covered:
- ✅ Training programming and progression
- ✅ Macronutrient targets and timing
- ✅ Micronutrient needs and sources
- ✅ Calorie calculation (BMR, TDEE, NEAT)
- ✅ Sleep and recovery optimization
- ✅ Evidence-based supplementation

## 🤖 Features

### Ask Coach Tab
- Interactive Q&A with evidence-based answers
- Automatic source citations and links
- Quick question buttons for common topics
- Query history tracking

### Learning Goals Tab
- Clear learning objectives and questions
- Progress tracking metrics
- Module completion status

### Corpus Explorer Tab
- Browse and filter all sources
- Search by keywords
- View source metadata and links

### Query History Tab
- Track all interactions
- Export conversation history
- Review past questions and answers

## 🔧 Technical Details

### RAG Pipeline (`src/rag_pipeline.py`)
```python
# Initialize system
from src.rag_pipeline import FitScienceRAG

rag = FitScienceRAG()
rag.initialize_system()

# Query the system
result = rag.query("How much protein should I eat?")
```

### Key Classes:
- `FitScienceRAG`: Main RAG system class
- Handles corpus loading, embedding, and retrieval
- Supports both OpenAI and retrieval-only modes

### Vector Store:
- **Embeddings**: HuggingFace sentence-transformers
- **Storage**: FAISS for fast similarity search
- **Chunking**: 1000 chars with 200 overlap

## 📈 Evaluation

The system supports evaluation using:
- **RAGAs**: Measure factuality, groundedness, context recall
- **ARES**: Alternative evaluation framework
- **Manual Assessment**: Review answer quality and source relevance

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

## 🔮 Future Enhancements

### Optional Bonus Features:
- **Reasoning Agents**: Chain-of-thought reasoning for complex queries
- **Multi-Agent Workflow**: Planner → Searcher → Summarizer pipeline
- **Knowledge Graph**: Neo4j integration for concept relationships

### Additional Features:
- User profile and goal tracking
- Personalized plan generation
- Integration with fitness tracking apps
- Advanced evaluation metrics

## 📊 Evaluation & Performance

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
python src/ragas_evaluation_v3.py
```

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

## 🤝 Contributing

This is an academic project for Assignment 3. For improvements:
1. Add more diverse sources to the corpus
2. Implement advanced evaluation metrics
3. Enhance the user interface
4. Add personalized recommendation features

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
- `rag_pipeline.py` - RAG system with hybrid LLM support (OpenAI GPT-4o-mini + Llama 3.2 1B)
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

## 📄 License

Academic project - see assignment guidelines for usage terms.

---

**FitScience Coach** - Making evidence-based fitness and nutrition accessible to everyone! 🏋️‍♀️💪
