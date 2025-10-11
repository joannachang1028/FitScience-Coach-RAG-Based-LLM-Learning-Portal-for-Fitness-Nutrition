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
- **LLM**: OpenAI GPT (optional, with fallback to retrieval-only)
- **Interface**: Streamlit web app

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
streamlit run streamlit_app.py
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

### RAG Pipeline (`rag_pipeline.py`)
```python
# Initialize system
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

- ✅ **System Code**: `rag_pipeline.py`, `streamlit_app.py`
- ✅ **Learning Corpus**: `learning_corpus.csv` (23 sources)
- ✅ **PLP Interface**: Streamlit web application
- ✅ **Documentation**: This README + step documentation
- 🔄 **Evaluation Logs**: In progress
- 🔄 **Final Report**: In progress

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

## 📄 License

Academic project - see assignment guidelines for usage terms.

---

**FitScience Coach** - Making evidence-based fitness and nutrition accessible to everyone! 🏋️‍♀️💪
