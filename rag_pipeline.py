"""
FitScience Coach - RAG Pipeline
Personal Learning Portal for Evidence-Based Fitness & Nutrition
"""

import os
import pandas as pd
import numpy as np
from typing import List, Dict, Any
import json
from datetime import datetime

# LangChain imports
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.schema import Document
import requests

# Streamlit for demo
import streamlit as st

class FitScienceRAG:
    def __init__(self, use_llama: bool = True):
        """Initialize the RAG system for FitScience Coach"""
        self.use_llama = use_llama
        
        # Initialize components
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
        
        # Use sentence transformers for embeddings (free)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2"
        )
        
        self.vectorstore = None
        self.qa_chain = None
        self.corpus_metadata = []
        self.llm = None
        
    def load_corpus_from_csv(self, csv_path: str = "learning_corpus.csv"):
        """Load learning corpus from CSV file"""
        try:
            df = pd.read_csv(csv_path)
            self.corpus_metadata = df.to_dict('records')
            print(f"✅ Loaded {len(self.corpus_metadata)} sources from corpus")
            return df
        except Exception as e:
            print(f"❌ Error loading corpus: {e}")
            return None
    
    def create_synthetic_content(self):
        """Create synthetic content for demo purposes based on corpus metadata"""
        documents = []
        
        # Sample content templates based on the corpus
        content_templates = {
            "protein_requirements": """
            Protein Requirements for Resistance Training:
            
            Based on meta-analyses, the optimal protein intake for resistance training is 1.6-2.2g per kg bodyweight per day. 
            This supports muscle protein synthesis and recovery. Protein should be distributed throughout the day, 
            with 20-40g per meal to maximize muscle protein synthesis rates.
            
            Key findings from Morton et al. (2017) meta-analysis show that protein intakes above 1.6g/kg/day 
            provide diminishing returns for muscle hypertrophy. Timing around workouts is less critical than 
            total daily intake, but consuming protein within 2 hours post-workout can enhance recovery.
            """,
            
            "bmr_calculation": """
            Basal Metabolic Rate (BMR) Calculation:
            
            BMR represents the calories your body burns at rest. The Harris-Benedict equation is commonly used:
            - Men: BMR = 88.362 + (13.397 × weight in kg) + (4.799 × height in cm) - (5.677 × age in years)
            - Women: BMR = 447.593 + (9.247 × weight in kg) + (3.098 × height in cm) - (4.330 × age in years)
            
            For activity levels, multiply BMR by:
            - Sedentary: 1.2 (little/no exercise)
            - Lightly active: 1.375 (light exercise 1-3 days/week)
            - Moderately active: 1.55 (moderate exercise 3-5 days/week)
            - Very active: 1.725 (hard exercise 6-7 days/week)
            - Extremely active: 1.9 (very hard exercise, physical job)
            """,
            
            "training_progression": """
            Progressive Overload in Strength Training:
            
            Progressive overload is the gradual increase of stress placed on the body during training. 
            This can be achieved through:
            1. Increasing weight (most common)
            2. Increasing reps with same weight
            3. Increasing sets
            4. Decreasing rest periods
            5. Increasing training frequency
            
            For beginners, aim for 2-3 sets of 8-12 reps, 2-3 times per week per muscle group.
            Progress should be consistent but gradual - typically 2.5-5lb increases weekly for compound movements.
            
            Recovery is crucial. Allow 48-72 hours between training the same muscle groups.
            """,
            
            "micronutrients": """
            Essential Micronutrients for Fitness:
            
            Key vitamins and minerals for active individuals:
            - Vitamin D: Important for muscle function and bone health. 1000-2000 IU daily recommended.
            - Magnesium: Supports muscle contraction and energy production. 400-600mg daily.
            - Iron: Critical for oxygen transport. Women need 18mg, men 8mg daily.
            - Zinc: Supports immune function and protein synthesis. 8-11mg daily.
            - B-vitamins: Essential for energy metabolism and recovery.
            
            Best sources are whole foods, but supplements can help fill gaps. 
            Consider a multivitamin if diet is inconsistent.
            """,
            
            "omega3_supplements": """
            Omega-3 Fatty Acids and Fish Oil:
            
            Omega-3 fatty acids (EPA and DHA) are essential fats that support heart health, brain function, and inflammation control.
            For general health: 1-2g daily (1000-2000mg)
            For cardiovascular benefits: 2-4g daily
            For athletes: 2-3g daily may help with recovery and inflammation
            
            Look for supplements with high EPA/DHA content (500mg+ combined per capsule).
            Take with meals to improve absorption and reduce fishy aftertaste.
            Quality matters - choose reputable brands with third-party testing.
            
            If you eat fatty fish (salmon, mackerel, sardines) 2-3 times per week, you may need less supplementation.
            """,
            
            "neat_activity": """
            NEAT (Non-Exercise Activity Thermogenesis):
            
            NEAT includes all daily activities outside of formal exercise: walking, fidgeting, 
            standing, household chores, etc. NEAT can vary by 200-900 calories daily between individuals.
            
            To increase NEAT:
            - Take stairs instead of elevators
            - Walk during phone calls
            - Use a standing desk
            - Park farther from destinations
            - Do household chores actively
            
            Tracking steps (aim for 8,000-12,000 daily) is a good NEAT proxy.
            """,
            
            "sleep_recovery": """
            Sleep and Athletic Recovery:
            
            Sleep is crucial for athletic performance and recovery. Adults need 7-9 hours of quality sleep nightly.
            During sleep, the body releases growth hormone, repairs muscle tissue, and consolidates motor learning.
            
            Poor sleep negatively affects:
            - Muscle protein synthesis
            - Immune function
            - Cognitive performance
            - Injury risk
            - Appetite regulation
            
            For optimal sleep:
            - Maintain consistent sleep schedule
            - Create cool, dark environment (65-68°F)
            - Avoid screens 1 hour before bed
            - Limit caffeine after 2pm
            - Consider meditation or relaxation techniques
            """,
            
            "workout_splits": """
            Training Program Design and Workout Splits:
            
            Effective workout splits depend on training experience and goals:
            
            Beginners: Full-body workouts 2-3x per week
            - Focus on compound movements
            - 2-3 sets of 8-12 reps
            - Allow 48-72 hours between sessions
            
            Intermediate: Upper/lower split 4x per week
            - Monday: Upper body
            - Tuesday: Lower body
            - Thursday: Upper body
            - Friday: Lower body
            
            Advanced: Push/pull/legs or body part splits
            - Push: Chest, shoulders, triceps
            - Pull: Back, biceps
            - Legs: Quads, hamstrings, glutes
            
            Key principles:
            - Train each muscle group 2-3x per week
            - Progressive overload
            - Adequate recovery between sessions
            - Focus on compound movements first
            """
        }
        
        # Create documents with metadata
        for i, source in enumerate(self.corpus_metadata):
            # Map sources to content templates
            content_key = None
            title_lower = source['Title'].lower()
            
            if 'protein' in title_lower:
                content_key = 'protein_requirements'
            elif 'bmr' in title_lower or 'metabolic' in title_lower:
                content_key = 'bmr_calculation'
            elif 'training' in title_lower or 'workout' in title_lower or 'progressive' in title_lower or 'resistance' in title_lower:
                content_key = 'training_progression'
            elif 'split' in title_lower or 'best workout' in title_lower:
                content_key = 'workout_splits'
            elif 'micronutrient' in title_lower or 'vitamin' in title_lower or 'supplement' in title_lower:
                content_key = 'micronutrients'
            elif 'omega' in title_lower or 'fish oil' in title_lower:
                content_key = 'omega3_supplements'
            elif 'neat' in title_lower or 'activity' in title_lower:
                content_key = 'neat_activity'
            elif 'sleep' in title_lower:
                content_key = 'sleep_recovery'
            elif 'energy' in title_lower or 'calorie' in title_lower or 'balance' in title_lower:
                content_key = 'bmr_calculation'
            elif 'periodization' in title_lower:
                content_key = 'training_progression'
            elif 'nutrition' in title_lower or 'performance' in title_lower:
                content_key = 'protein_requirements'
            elif 'cavaliere' in title_lower or 'athlean' in title_lower:
                content_key = 'workout_splits'
            elif 'jamnadas' in title_lower or 'visceral' in title_lower or 'fat' in title_lower:
                content_key = 'bmr_calculation'
            elif 'attia' in title_lower or 'longevity' in title_lower:
                content_key = 'training_progression'
            elif 'probiotic' in title_lower or 'metabolic' in title_lower:
                content_key = 'micronutrients'
            elif 'myplate' in title_lower or 'nhs' in title_lower or 'nih' in title_lower:
                content_key = 'micronutrients'
            else:
                # Generic content for other sources - use training progression as safer default
                content_key = 'training_progression'
            
            if content_key in content_templates:
                doc = Document(
                    page_content=content_templates[content_key],
                    metadata={
                        'source': source['Title'],
                        'url': source['URL'],
                        'type': source['Type'],
                        'relevance': source['Relevance'],
                        'notes': source['Notes']
                    }
                )
                documents.append(doc)
        
        return documents
    
    def build_vectorstore(self, documents: List[Document]):
        """Build FAISS vector store from documents"""
        try:
            print("🔄 Building vector store...")
            self.vectorstore = FAISS.from_documents(documents, self.embeddings)
            print(f"✅ Vector store built with {len(documents)} documents")
            return True
        except Exception as e:
            print(f"❌ Error building vector store: {e}")
            return False
    
    def setup_qa_chain(self):
        """Setup retriever and LLM for QA with citations"""
        if not self.vectorstore:
            print("❌ Vector store not initialized")
            return False

        try:
            # Initialize Ollama connection
            if self.use_llama:
                print("🦙 Checking Ollama connection...")
                try:
                    # Test Ollama connection
                    response = requests.get("http://localhost:11434/api/tags", timeout=3)
                    if response.status_code == 200:
                        models = response.json().get('models', [])
                        llama_model = any('llama3.2:1b' in model.get('name', '') for model in models)
                        
                        if llama_model:
                            self.llm = "ollama"  # Flag for Ollama usage
                            print("✅ Llama 3.2 1B via Ollama ready")
                        else:
                            print("⚠️ Llama 3.2 1B not found - will use corpus-only mode")
                            self.llm = None
                    else:
                        print("⚠️ Ollama not responding - will use corpus-only mode")
                        self.llm = None
                except requests.exceptions.RequestException:
                    print("⚠️ Ollama not available - will use corpus-only mode")
                    self.llm = None
            else:
                print("⚠️ Ollama disabled. Using corpus-only mode.")
                self.llm = None

            # Keep retriever available with adaptive retrieval
            self.qa_chain = self.vectorstore.as_retriever(search_kwargs={"k": 8})
            print("✅ QA components ready")
            return True
        except Exception as e:
            print(f"❌ Error setting up QA components: {e}")
            return False
    
    def calculate_bmr(self, weight_kg: float, height_cm: float, age: int, gender: str) -> float:
        """Calculate BMR using Harris-Benedict equation"""
        if gender.lower() in ['male', 'm', 'man']:
            bmr = 88.362 + (13.397 * weight_kg) + (4.799 * height_cm) - (5.677 * age)
        elif gender.lower() in ['female', 'f', 'woman']:
            bmr = 447.593 + (9.247 * weight_kg) + (3.098 * height_cm) - (4.330 * age)
        else:
            raise ValueError("Gender must be 'male' or 'female'")
        return round(bmr, 1)
    
    def calculate_tdee(self, bmr: float, activity_level: str) -> float:
        """Calculate TDEE from BMR and activity level"""
        activity_multipliers = {
            'sedentary': 1.2,           # Little/no exercise
            'lightly_active': 1.375,    # Light exercise 1-3 days/week
            'moderately_active': 1.55,  # Moderate exercise 3-5 days/week
            'very_active': 1.725,       # Hard exercise 6-7 days/week
            'extremely_active': 1.9     # Very hard exercise, physical job
        }
        
        activity_level_lower = activity_level.lower().replace(' ', '_')
        if activity_level_lower in activity_multipliers:
            tdee = bmr * activity_multipliers[activity_level_lower]
            return round(tdee, 1)
        else:
            raise ValueError(f"Invalid activity level. Choose from: {list(activity_multipliers.keys())}")
    
    def generate_ollama_response(self, context: str, question: str, docs=None) -> str:
        """Generate response using Llama 3.2 1B via Ollama"""
        try:
            # Format prompt for Llama 3.2 - natural, conversational responses
            prompt = f"""You are FitScience Coach, a specialized fitness and nutrition expert. You have access to curated research sources AND general fitness knowledge.

Always provide a comprehensive answer that combines both sources of information. Be conversational, practical, and encouraging.

Research Sources from my Knowledge Base:
{context}

User Question: {question}

Instructions:
1. Provide a helpful, comprehensive answer using both the research sources above AND your general knowledge
2. Be conversational and encouraging
3. Give practical, actionable advice
4. At the end, add a 'Sources' section listing any research sources you used from the provided context

Answer:"""
            
            # Call Ollama API
            payload = {
                "model": "llama3.2:1b",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 512
                }
            }
            
            response = requests.post(
                "http://localhost:11434/api/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', 'No response generated').strip()
            else:
                return f"Ollama API error: {response.status_code} - {response.text}"
            
        except requests.exceptions.RequestException as e:
            return f"Error connecting to Ollama: {e}"
        except Exception as e:
            return f"Error generating Ollama response: {e}"
    
    def query(self, question: str) -> Dict[str, Any]:
        """Query the RAG system with LLM answer and explicit source links"""
        if not self.qa_chain:
            return {"error": "QA chain not initialized"}
        
        try:
            # Retrieve relevant docs
            docs = self.qa_chain.invoke(question)
            print(f"📚 Initial search found {len(docs)} relevant sources for: '{question[:50]}...'")

            # If no relevant docs found, try broader search terms
            if len(docs) == 0:
                print("🔍 No relevant sources found, trying broader search...")
                # Try searching with key terms from the question
                question_words = question.lower().split()
                key_terms = [word for word in question_words if len(word) > 3 and word not in ['what', 'how', 'when', 'where', 'why', 'should', 'would', 'could', 'will', 'does', 'doesn', 'don', 'isn', 'aren', 'wasn', 'weren', 'haven', 'hasn', 'hadn', 'won', 'can', 'can\'t']]
                
                if key_terms:
                    # Try searching with the most relevant terms
                    search_terms = " ".join(key_terms[:3])  # Use top 3 terms
                    docs = self.qa_chain.invoke(search_terms)
                    print(f"🔍 Broader search with terms '{search_terms}' found {len(docs)} sources")

            # Build context with sources
            context_lines = []
            for idx, d in enumerate(docs, 1):
                title = d.metadata.get('source', f'Source {idx}')
                url = d.metadata.get('url', '')
                note = d.metadata.get('notes', d.metadata.get('relevance', ''))
                context_lines.append(f"[{idx}] {title} | {url} | {note}\n{d.page_content[:800]}")

            context_text = "\n\n".join(context_lines)

            # Always use LLM to generate answer (corpus + general knowledge)
            print(f"📚 Using {len(docs)} relevant sources in final answer")
            answer = self._generate_llm_answer(context_text, question, docs)

            return {
                "answer": answer,
                "sources": [
                    {
                        "title": d.metadata.get('source', 'Unknown'),
                        "url": d.metadata.get('url', ''),
                        "type": d.metadata.get('type', ''),
                        "relevance": d.metadata.get('relevance', ''),
                        "notes": d.metadata.get('notes', ''),
                        "content_preview": d.page_content[:200] + "..."
                    }
                    for d in docs
                ]
            }
        except Exception as e:
            return {"error": f"Query failed: {e}"}
    
    def _generate_llm_answer(self, context_text: str, question: str, docs) -> str:
        """Generate answer using LLM with corpus context + general knowledge"""
        # Try to get Ollama working
        if self.llm == "ollama":
            return self.generate_ollama_response(context_text, question, docs)
        else:
            # Try to connect to Ollama
            if self.use_llama:
                print("🦙 Attempting to connect to Ollama...")
                try:
                    response = requests.get("http://localhost:11434/api/tags", timeout=3)
                    if response.status_code == 200:
                        models = response.json().get('models', [])
                        llama_model = any('llama3.2:1b' in model.get('name', '') for model in models)
                        
                        if llama_model:
                            print("✅ Ollama connected! Generating answer...")
                            self.llm = "ollama"
                            return self.generate_ollama_response(context_text, question, docs)
                except:
                    pass
            
            # If no LLM available, show helpful message
            return self._no_llm_message(docs)
    
    
    def _no_llm_message(self, docs) -> str:
        """Show helpful message when no LLM is available"""
        if not docs:
            return ("I need Ollama with Llama 3.2 1B to provide comprehensive answers. Please:\n\n"
                   "**Setup Instructions:**\n"
                   "• Install: `curl -fsSL https://ollama.com/install.sh | sh`\n"
                   "• Pull model: `ollama pull llama3.2:1b`\n"
                   "• Start: `ollama serve`\n"
                   "• Click 'Apply Settings' in the sidebar")
        
        return ("I found relevant sources in my knowledge base, but I need Ollama with Llama 3.2 1B to provide comprehensive answers.\n\n"
               "**To get AI-powered answers:**\n"
               "• Install Ollama: `curl -fsSL https://ollama.com/install.sh | sh`\n"
               "• Pull model: `ollama pull llama3.2:1b`\n"
               "• Start Ollama: `ollama serve`\n"
               "• Click 'Apply Settings' in the sidebar\n\n"
               "**Sources found in my knowledge base:**\n" +
               "\n".join([f"• {d.metadata.get('source', 'Unknown')}" for d in docs[:3]]))
    
    def _simple_corpus_response(self, docs, question):
        """Simple fallback response when no LLM is available"""
        if not docs:
            return {
                "answer": "I couldn't find specific information about your question in my knowledge base. Please try rephrasing your question or ask about training, nutrition, supplements, or health topics.",
                "sources": []
            }
        
        # Simple response from corpus
        answer = "Based on the research in my knowledge base:\n\n"
        unique_content = []
        seen_content = set()
        
        for d in docs:
            content_sig = d.page_content[:150].strip()
            if content_sig not in seen_content and len(content_sig) > 30:
                seen_content.add(content_sig)
                clean_content = d.page_content[:400].replace('\n', ' ').strip()
                unique_content.append(clean_content)
        
        if unique_content:
            answer += "\n\n".join(unique_content[:2])
        else:
            answer += docs[0].page_content[:400].replace('\n', ' ').strip()
        
        # Add sources
        answer += f"\n\n**Sources:**\n"
        for d in docs[:4]:
            source_name = d.metadata.get('source', 'Unknown Source')
            source_url = d.metadata.get('url', '')
            if source_url and source_url != '':
                answer += f"- [{source_name}]({source_url})\n"
            else:
                answer += f"- {source_name}\n"
        
        return {
            "answer": answer,
            "sources": [
                {
                    "title": d.metadata.get('source', 'Unknown'),
                    "url": d.metadata.get('url', ''),
                    "type": d.metadata.get('type', ''),
                    "relevance": d.metadata.get('relevance', ''),
                    "notes": d.metadata.get('notes', ''),
                    "content_preview": d.page_content[:200] + "..."
                }
                for d in docs
            ]
        }
    
    def initialize_system(self):
        """Initialize the complete RAG system"""
        print("🚀 Initializing FitScience Coach RAG System...")
        
        # Load corpus
        corpus_df = self.load_corpus_from_csv()
        if corpus_df is None:
            return False
        
        # Create synthetic content for demo
        documents = self.create_synthetic_content()
        
        # Build vector store
        if not self.build_vectorstore(documents):
            return False
        
        # Setup QA chain
        if not self.setup_qa_chain():
            return False
        
        print("✅ FitScience Coach RAG System ready!")
        return True

def main():
    """Demo function"""
    rag = FitScienceRAG()
    
    if rag.initialize_system():
        # Demo queries
        demo_questions = [
            "How much protein should I eat for muscle building?",
            "How do I calculate my daily calorie needs?",
            "What is progressive overload in training?",
            "What micronutrients are important for athletes?",
            "How much fish oil should I take per day?"
        ]
        
        for question in demo_questions:
            print(f"\n❓ Question: {question}")
            result = rag.query(question)
            
            if "error" not in result:
                print(f"💡 Answer: {result['answer'][:200]}...")
                print(f"📚 Sources: {len(result['sources'])} found")
                for source in result['sources']:
                    print(f"   - {source['title']}")
            else:
                print(f"❌ Error: {result['error']}")

if __name__ == "__main__":
    main()