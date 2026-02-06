"""
FitScience Coach - Streamlit Interface
Personal Learning Portal for Evidence-Based Fitness & Nutrition
"""

import os
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import pandas as pd
from rag_pipeline import FitScienceRAG
import json
from datetime import datetime

# Page config
st.set_page_config(
    page_title="FitScience Coach",
    page_icon="🏋️‍♀️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2E8B57;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #4682B4;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .source-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #2E8B57;
    }
    .answer-box {
        background-color: #e8f5e8;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #2E8B57;
        margin: 1rem 0;
    }
    .metric-box {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
        border: 1px solid #dee2e6;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'rag_system' not in st.session_state:
    st.session_state.rag_system = None
if 'corpus_data' not in st.session_state:
    st.session_state.corpus_data = None
if 'query_history' not in st.session_state:
    st.session_state.query_history = []
if 'openai_api_key' not in st.session_state:
    st.session_state.openai_api_key = os.getenv("OPENAI_API_KEY", "")
if 'groq_api_key' not in st.session_state:
    st.session_state.groq_api_key = os.getenv("GROQ_API_KEY", "")
if 'use_groq' not in st.session_state:
    st.session_state.use_groq = True
if 'current_question' not in st.session_state:
    st.session_state.current_question = ""
if 'auto_trigger' not in st.session_state:
    st.session_state.auto_trigger = False
if 'question_counter' not in st.session_state:
    st.session_state.question_counter = 0
if 'last_question' not in st.session_state:
    st.session_state.last_question = ""
# BMR Calculator session state initialization
if 'bmr_activity_level' not in st.session_state:
    st.session_state.bmr_activity_level = "Moderately Active"
if 'bmr_neat_level' not in st.session_state:
    st.session_state.bmr_neat_level = "Moderate"
if 'bmr_gender' not in st.session_state:
    st.session_state.bmr_gender = "Male"
if 'bmr_age' not in st.session_state:
    st.session_state.bmr_age = 25
if 'bmr_weight' not in st.session_state:
    st.session_state.bmr_weight = 70.0
if 'bmr_height' not in st.session_state:
    st.session_state.bmr_height = 175.0
# Initialize all BMR widget session state
if 'bmr_activity_level_selectbox' not in st.session_state:
    st.session_state.bmr_activity_level_selectbox = "Moderately Active"
if 'bmr_neat_level_selectbox' not in st.session_state:
    st.session_state.bmr_neat_level_selectbox = "Moderate"
if 'bmr_gender_radio' not in st.session_state:
    st.session_state.bmr_gender_radio = "Male"
if 'bmr_age_input' not in st.session_state:
    st.session_state.bmr_age_input = 25
if 'bmr_weight_unit_radio' not in st.session_state:
    st.session_state.bmr_weight_unit_radio = "kg"
if 'bmr_weight_kg_input' not in st.session_state:
    st.session_state.bmr_weight_kg_input = 70.0
if 'bmr_weight_lbs_input' not in st.session_state:
    st.session_state.bmr_weight_lbs_input = 154.0
if 'bmr_height_unit_radio' not in st.session_state:
    st.session_state.bmr_height_unit_radio = "cm"
if 'bmr_height_cm_input' not in st.session_state:
    st.session_state.bmr_height_cm_input = 175.0
if 'bmr_height_ft_input' not in st.session_state:
    st.session_state.bmr_height_ft_input = 5
if 'bmr_height_in_input' not in st.session_state:
    st.session_state.bmr_height_in_input = 9

@st.cache_data
def load_corpus_data():
    """Load and cache corpus data"""
    try:
        df = pd.read_csv("data/learning_corpus.csv")
        return df
    except Exception as e:
        st.error(f"Error loading corpus: {e}")
        return None

def initialize_rag_system():
    """Initialize the RAG system"""
    if st.session_state.rag_system is None:
        with st.spinner("🚀 Initializing FitScience Coach..."):
            rag = FitScienceRAG(
                use_groq=st.session_state.use_groq,
                openai_api_key=st.session_state.openai_api_key or None,
                groq_api_key=st.session_state.groq_api_key or None
            )
            if rag.initialize_system():
                st.session_state.rag_system = rag
                st.success("✅ System ready!")
                return True
            else:
                st.error("❌ Failed to initialize system")
                return False
    return True

def main():
    # Header
    st.markdown('<h1 class="main-header">🏋️‍♀️ FitScience Coach</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">Your Evidence-Based Fitness & Nutrition Portal</p>', unsafe_allow_html=True)
    
    # Initialize systems
    if not initialize_rag_system():
        st.stop()
    
    # Load corpus data
    if st.session_state.corpus_data is None:
        st.session_state.corpus_data = load_corpus_data()
    
    # Sidebar
    with st.sidebar:
        # Learning Dashboard
        if st.session_state.corpus_data is not None:
            # Initialize session state for learning progress
            if 'learning_progress' not in st.session_state:
                st.session_state.learning_progress = {}
            if 'completed_modules' not in st.session_state:
                st.session_state.completed_modules = set()
            if 'current_learning_path' not in st.session_state:
                st.session_state.current_learning_path = []
            
            st.markdown("### 📊 Learning Dashboard")
            
            # Overall Progress - Now calculated dynamically across all learning paths
            overall_progress = st.session_state.get('overall_progress', 0.0)
            st.metric("Overall Progress", f"{overall_progress:.1f}%")
            st.progress(overall_progress / 100)
            
            st.markdown("### 🎯 Learning Paths")
            
            # Function to calculate actual module count for a learning path
            def calculate_module_count(path_name, corpus_data, path_topics=None):
                # Filter data by learning path topics first (same as main content area)
                if path_topics:
                    path_data = corpus_data[
                        corpus_data['Title'].str.contains('|'.join(path_topics), case=False, na=False) |
                        corpus_data['Notes'].str.contains('|'.join(path_topics), case=False, na=False)
                    ]
                else:
                    path_data = corpus_data
                
                if path_name == "🏋️‍♂️ Strength Training Fundamentals":
                    # Training principles
                    training_sources = path_data[
                        (path_data['Title'].str.contains('progressive overload|resistance training|periodization|training volume', case=False, na=False)) |
                        (path_data['Notes'].str.contains('progressive overload|resistance training|periodization|training volume', case=False, na=False))
                    ]
                    # Expert insights
                    expert_sources = path_data[
                        (path_data['Type'] == 'Podcast') & 
                        (path_data['Title'].str.contains('Jeff Cavaliere|training|exercise|workout', case=False, na=False))
                    ]
                    # Government resources
                    gov_sources = path_data[path_data['Type'] == 'Government Resource']
                    
                    count = 0
                    if len(training_sources) > 0: count += 1
                    if len(expert_sources) > 0: count += 1
                    if len(gov_sources) > 0: count += 1
                    return count
                    
                elif path_name == "🥗 Sports Nutrition Mastery":
                    # Protein sources
                    protein_sources = path_data[
                        (path_data['Title'].str.contains('protein|nutrition', case=False, na=False)) |
                        (path_data['Notes'].str.contains('protein|nutrition', case=False, na=False))
                    ]
                    # Supplement sources
                    supplement_sources = path_data[
                        (path_data['Title'].str.contains('supplement|micronutrient|vitamin', case=False, na=False)) |
                        (path_data['Notes'].str.contains('supplement|micronutrient|vitamin', case=False, na=False))
                    ]
                    # Government resources
                    gov_sources = path_data[path_data['Type'] == 'Government Resource']
                    
                    count = 0
                    if len(protein_sources) > 0: count += 1
                    if len(supplement_sources) > 0: count += 1
                    if len(gov_sources) > 0: count += 1
                    return count
                    
                elif path_name == "🔥 Metabolic Science":
                    # BMR sources
                    bmr_sources = path_data[
                        (path_data['Title'].str.contains('BMR|metabolic|energy|calorie', case=False, na=False)) |
                        (path_data['Notes'].str.contains('BMR|metabolic|energy|calorie', case=False, na=False))
                    ]
                    # NEAT sources
                    neat_sources = path_data[
                        (path_data['Title'].str.contains('NEAT|activity', case=False, na=False)) |
                        (path_data['Notes'].str.contains('NEAT|activity', case=False, na=False))
                    ]
                    # Government resources
                    gov_sources = path_data[path_data['Type'] == 'Government Resource']
                    
                    count = 0
                    if len(bmr_sources) > 0: count += 1
                    if len(neat_sources) > 0: count += 1
                    if len(gov_sources) > 0: count += 1
                    return count
                    
                elif path_name == "💤 Recovery & Performance":
                    # Sleep sources
                    sleep_sources = path_data[
                        (path_data['Title'].str.contains('sleep|recovery|athletic performance', case=False, na=False)) |
                        (path_data['Notes'].str.contains('sleep|recovery|athletic performance', case=False, na=False))
                    ]
                    # Performance sources
                    performance_sources = path_data[
                        (path_data['Type'] == 'Podcast') & 
                        (path_data['Title'].str.contains('Dr. Peter Attia|performance|longevity', case=False, na=False))
                    ]
                    # Government resources
                    gov_sources = path_data[path_data['Type'] == 'Government Resource']
                    
                    count = 0
                    if len(sleep_sources) > 0: count += 1
                    if len(performance_sources) > 0: count += 1
                    if len(gov_sources) > 0: count += 1
                    return count
                    
                return 0
            
            # Define structured learning paths (like Coursera specializations)
            learning_paths = {
                "🏋️‍♂️ Strength Training Fundamentals": {
                    "description": "Master the science of resistance training",
                    "topics": ["progressive overload", "resistance training", "workout split", "training", "periodization"],
                    "estimated_time": "2-3 hours",
                    "difficulty": "Beginner to Intermediate"
                },
                "🥗 Sports Nutrition Mastery": {
                    "description": "Evidence-based nutrition for athletes",
                    "topics": ["protein", "nutrition", "dietary", "micronutrient", "supplement"],
                    "estimated_time": "2-3 hours", 
                    "difficulty": "Intermediate"
                },
                "🔥 Metabolic Science": {
                    "description": "Understand energy systems and metabolism",
                    "topics": ["BMR", "metabolic", "energy", "calorie", "NEAT"],
                    "estimated_time": "2-3 hours",
                    "difficulty": "Intermediate to Advanced"
                },
                "💤 Recovery & Performance": {
                    "description": "Optimize sleep and athletic recovery",
                    "topics": ["sleep", "recovery", "athletic performance"],
                    "estimated_time": "1-2 hours",
                    "difficulty": "Beginner"
                }
            }
            
            # Calculate module counts for each learning path
            for path_name, path_info in learning_paths.items():
                path_info["modules"] = calculate_module_count(path_name, st.session_state.corpus_data, path_info["topics"])
            
            # Function to calculate overall progress across all learning paths
            def calculate_overall_progress():
                """Calculate overall progress across all learning paths"""
                total_lessons_all_paths = 0
                completed_lessons_all_paths = 0
                
                for path_name, path_info in learning_paths.items():
                    # Get path topics
                    path_topics = path_info.get('topics', [])
                    
                    # Filter corpus data for this path
                    if path_topics:
                        path_data = st.session_state.corpus_data[
                            st.session_state.corpus_data['Title'].str.contains('|'.join(path_topics), case=False, na=False) |
                            st.session_state.corpus_data['Notes'].str.contains('|'.join(path_topics), case=False, na=False)
                        ]
                    else:
                        path_data = st.session_state.corpus_data
                    
                    # Calculate modules and lessons for this path (same logic as main content)
                    modules = {}
                    if path_name == "🏋️‍♂️ Strength Training Fundamentals":
                        # Training principles
                        training_sources = path_data[
                            (path_data['Title'].str.contains('progressive overload|resistance training|periodization|training volume', case=False, na=False)) |
                            (path_data['Notes'].str.contains('progressive overload|resistance training|periodization|training volume', case=False, na=False))
                        ]
                        if len(training_sources) > 0:
                            modules["Training Principles & Progression"] = {"sources": training_sources}
                        
                        # Expert insights
                        expert_sources = path_data[
                            (path_data['Type'] == 'Podcast') & 
                            (path_data['Title'].str.contains('Jeff Cavaliere|training|exercise|workout', case=False, na=False))
                        ]
                        if len(expert_sources) > 0:
                            modules["Expert Training Insights"] = {"sources": expert_sources}
                        
                        # Government resources
                        gov_sources = path_data[path_data['Type'] == 'Government Resource']
                        if len(gov_sources) > 0:
                            modules["Official Training Guidelines"] = {"sources": gov_sources}
                    
                    elif path_name == "🥗 Sports Nutrition Mastery":
                        # Protein sources
                        protein_sources = path_data[
                            (path_data['Title'].str.contains('protein|nutrition', case=False, na=False)) |
                            (path_data['Notes'].str.contains('protein|nutrition', case=False, na=False))
                        ]
                        if len(protein_sources) > 0:
                            modules["Protein & Nutrition Science"] = {"sources": protein_sources}
                        
                        # Supplement sources
                        supplement_sources = path_data[
                            (path_data['Title'].str.contains('supplement|micronutrient|vitamin', case=False, na=False)) |
                            (path_data['Notes'].str.contains('supplement|micronutrient|vitamin', case=False, na=False))
                        ]
                        if len(supplement_sources) > 0:
                            modules["Evidence-Based Supplements"] = {"sources": supplement_sources}
                        
                        # Government resources
                        gov_sources = path_data[path_data['Type'] == 'Government Resource']
                        if len(gov_sources) > 0:
                            modules["Nutritional Guidelines"] = {"sources": gov_sources}
                    
                    elif path_name == "🔥 Metabolic Science":
                        # BMR sources
                        bmr_sources = path_data[
                            (path_data['Title'].str.contains('BMR|metabolic|energy|calorie', case=False, na=False)) |
                            (path_data['Notes'].str.contains('BMR|metabolic|energy|calorie', case=False, na=False))
                        ]
                        if len(bmr_sources) > 0:
                            modules["Energy Systems & BMR"] = {"sources": bmr_sources}
                        
                        # NEAT sources
                        neat_sources = path_data[
                            (path_data['Title'].str.contains('NEAT|activity', case=False, na=False)) |
                            (path_data['Notes'].str.contains('NEAT|activity', case=False, na=False))
                        ]
                        if len(neat_sources) > 0:
                            modules["Activity & NEAT"] = {"sources": neat_sources}
                        
                        # Government resources
                        gov_sources = path_data[path_data['Type'] == 'Government Resource']
                        if len(gov_sources) > 0:
                            modules["Metabolic Guidelines"] = {"sources": gov_sources}
                    
                    elif path_name == "💤 Recovery & Performance":
                        # Sleep sources
                        sleep_sources = path_data[
                            (path_data['Title'].str.contains('sleep|recovery|athletic performance', case=False, na=False)) |
                            (path_data['Notes'].str.contains('sleep|recovery|athletic performance', case=False, na=False))
                        ]
                        if len(sleep_sources) > 0:
                            modules["Sleep & Recovery Science"] = {"sources": sleep_sources}
                        
                        # Performance sources
                        performance_sources = path_data[
                            (path_data['Type'] == 'Podcast') & 
                            (path_data['Title'].str.contains('Dr. Peter Attia|performance|longevity', case=False, na=False))
                        ]
                        if len(performance_sources) > 0:
                            modules["Performance Optimization"] = {"sources": performance_sources}
                        
                        # Government resources
                        gov_sources = path_data[path_data['Type'] == 'Government Resource']
                        if len(gov_sources) > 0:
                            modules["Health Guidelines"] = {"sources": gov_sources}
                    
                    # Count lessons for this path
                    path_lessons = sum(len(module_info['sources']) for module_info in modules.values())
                    total_lessons_all_paths += path_lessons
                
                # Count completed lessons across all paths
                completed_lessons_all_paths = len([l for l in st.session_state.completed_modules if 'lesson' in l])
                
                if total_lessons_all_paths > 0:
                    return (completed_lessons_all_paths / total_lessons_all_paths) * 100
                else:
                    return 0.0
            
            # Calculate overall progress and store in session state
            overall_progress = calculate_overall_progress()
            st.session_state.overall_progress = overall_progress
            
            # Learning path selection
            selected_path = st.selectbox(
                "Choose Your Learning Path:",
                list(learning_paths.keys()),
                format_func=lambda x: x
            )
            
            if selected_path:
                path_info = learning_paths[selected_path]
                st.markdown(f"**{path_info['description']}**")
                st.markdown(f"📚 {path_info['modules']} modules")
                st.markdown(f"⏱️ {path_info['estimated_time']}")
                st.markdown(f"📈 {path_info['difficulty']}")
            
            st.markdown("---")
        
        # LLM Settings - API key from .env, no user input needed
        st.subheader("🔑 LLM Settings")
        if st.session_state.groq_api_key:
            st.success("🦙 Groq Llama ready — AI answers enabled")
        else:
            st.warning("Add GROQ_API_KEY to .env to enable AI answers")
        st.session_state.use_groq = True
        
        if st.session_state.corpus_data is not None:
            # Corpus statistics
            total_sources = len(st.session_state.corpus_data)
            academic_papers = len(st.session_state.corpus_data[st.session_state.corpus_data['Type'] == 'Academic Paper'])
            podcasts = len(st.session_state.corpus_data[st.session_state.corpus_data['Type'] == 'Podcast'])
            government_resources = len(st.session_state.corpus_data[st.session_state.corpus_data['Type'] == 'Government Resource'])
            
            st.header("📚 Learning Corpus")
            st.metric("Total Sources", total_sources)
            st.metric("Academic Papers", academic_papers)
            st.metric("Podcasts", podcasts)
            st.metric("Government Resources", government_resources)
            
            # Source type breakdown
            st.subheader("㊮ Source Types")
            type_counts = st.session_state.corpus_data['Type'].value_counts()
            st.bar_chart(type_counts, color="#2E8B57")
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📚 Courses", "🤖 Ask Coach", "🧮 BMR Calculator", "📝 Query History"])
    
    
    with tab1:
        st.markdown('<h2 class="sub-header">🎓 Personal Learning Portal</h2>', unsafe_allow_html=True)
        
        if st.session_state.corpus_data is not None:
            # Initialize session state for learning progress
            if 'learning_progress' not in st.session_state:
                st.session_state.learning_progress = {}
            if 'completed_modules' not in st.session_state:
                st.session_state.completed_modules = set()
            if 'current_learning_path' not in st.session_state:
                st.session_state.current_learning_path = []
            
            # Main Learning Interface (Khan Academy/Coursera style)
            if selected_path:
                path_info = learning_paths[selected_path]
                path_topics = path_info['topics']
                
                # Filter sources for this learning path
                path_data = st.session_state.corpus_data[
                    st.session_state.corpus_data['Title'].str.contains('|'.join(path_topics), case=False, na=False) |
                    st.session_state.corpus_data['Notes'].str.contains('|'.join(path_topics), case=False, na=False)
                ]
                
                # Group sources into structured learning modules based on learning path
                modules = {}
                
                if selected_path == "🏋️‍♂️ Strength Training Fundamentals":
                    modules = {
                        "💪 Module 1: Training Principles & Progression": {
                            "description": "Master fundamental training concepts and progressive overload",
                            "sources": path_data[
                                (path_data['Title'].str.contains('progressive overload|resistance training|periodization|training volume', case=False, na=False)) |
                                (path_data['Notes'].str.contains('progressive overload|resistance training|periodization|training volume', case=False, na=False))
                            ],
                            "learning_objectives": ["Understand progressive overload principles", "Design training progression", "Apply periodization concepts"]
                        },
                        "🏋️‍♂️ Module 2: Expert Training Insights": {
                            "description": "Learn from strength training experts and practitioners",
                            "sources": path_data[
                                (path_data['Type'] == 'Podcast') & 
                                (path_data['Title'].str.contains('Jeff Cavaliere|training|exercise|workout', case=False, na=False))
                            ],
                            "learning_objectives": ["Gain expert training insights", "Learn practical programming", "Understand exercise selection"]
                        },
                        "📚 Module 3: Beginner Program Design": {
                            "description": "Apply structured training programs for beginners",
                            "sources": path_data[path_data['Type'] == 'Government Resource'],
                            "learning_objectives": ["Design beginner programs", "Implement safe progression", "Apply structured training"]
                        }
                    }
                
                elif selected_path == "🥗 Sports Nutrition Mastery":
                    modules = {
                        "🥩 Module 1: Protein Science & Requirements": {
                            "description": "Master protein needs for athletic performance",
                            "sources": path_data[
                                (path_data['Title'].str.contains('protein|nutrition', case=False, na=False)) |
                                (path_data['Notes'].str.contains('protein|nutrition', case=False, na=False))
                            ],
                            "learning_objectives": ["Calculate protein requirements", "Understand protein timing", "Apply protein strategies"]
                        },
                        "💊 Module 2: Supplement Evidence & Micronutrients": {
                            "description": "Navigate supplements and micronutrient needs",
                            "sources": path_data[
                                (path_data['Title'].str.contains('supplement|micronutrient|vitamin', case=False, na=False)) |
                                (path_data['Notes'].str.contains('supplement|micronutrient|vitamin', case=False, na=False))
                            ],
                            "learning_objectives": ["Evaluate supplement evidence", "Understand micronutrient needs", "Apply supplementation strategies"]
                        },
                        "🍽️ Module 3: Practical Nutrition Tools": {
                            "description": "Use official tools for meal planning and calorie targets",
                            "sources": path_data[path_data['Type'] == 'Government Resource'],
                            "learning_objectives": ["Plan balanced meals", "Calculate calorie needs", "Apply dietary guidelines"]
                        }
                    }
                
                elif selected_path == "🔥 Metabolic Science":
                    modules = {
                        "⚡ Module 1: Energy Systems & BMR": {
                            "description": "Understand metabolic rate and energy expenditure",
                            "sources": path_data[
                                (path_data['Title'].str.contains('BMR|metabolic|energy|calorie', case=False, na=False)) |
                                (path_data['Notes'].str.contains('BMR|metabolic|energy|calorie', case=False, na=False))
                            ],
                            "learning_objectives": ["Calculate BMR accurately", "Understand energy systems", "Apply metabolic principles"]
                        },
                        "🏃‍♂️ Module 2: NEAT & Activity Optimization": {
                            "description": "Optimize daily activity and energy expenditure",
                            "sources": path_data[
                                (path_data['Title'].str.contains('NEAT|activity', case=False, na=False)) |
                                (path_data['Notes'].str.contains('NEAT|activity', case=False, na=False))
                            ],
                            "learning_objectives": ["Understand NEAT principles", "Optimize daily activity", "Track energy expenditure"]
                        },
                        "📊 Module 3: Metabolic Calculations & Tools": {
                            "description": "Apply practical metabolic calculations and tools",
                            "sources": path_data[path_data['Type'] == 'Government Resource'],
                            "learning_objectives": ["Use metabolic calculators", "Apply energy balance", "Implement tracking methods"]
                        }
                    }
                
                elif selected_path == "💤 Recovery & Performance":
                    modules = {
                        "😴 Module 1: Sleep Science & Recovery": {
                            "description": "Understand sleep's role in athletic performance",
                            "sources": path_data[
                                (path_data['Title'].str.contains('sleep|recovery|athletic performance', case=False, na=False)) |
                                (path_data['Notes'].str.contains('sleep|recovery|athletic performance', case=False, na=False))
                            ],
                            "learning_objectives": ["Understand sleep physiology", "Optimize recovery protocols", "Apply sleep strategies"]
                        },
                        "🧠 Module 2: Performance Optimization Insights": {
                            "description": "Learn from performance and longevity experts",
                            "sources": path_data[
                                (path_data['Type'] == 'Podcast') & 
                                (path_data['Title'].str.contains('Dr. Peter Attia|performance|longevity', case=False, na=False))
                            ],
                            "learning_objectives": ["Understand performance optimization", "Learn longevity protocols", "Apply recovery strategies"]
                        },
                        "🏥 Module 3: Health & Recovery Guidelines": {
                            "description": "Apply evidence-based health and recovery guidelines",
                            "sources": path_data[path_data['Type'] == 'Government Resource'],
                            "learning_objectives": ["Follow health guidelines", "Implement recovery protocols", "Apply wellness practices"]
                        }
                    }
                
                # Filter out empty modules and update module count in learning path info
                modules = {k: v for k, v in modules.items() if len(v['sources']) > 0}
                
                # Update the module count in learning_paths to reflect actual modules
                if selected_path in learning_paths:
                    learning_paths[selected_path]["modules"] = len(modules)
                
                # Learning Path Header (Coursera style) - NOW WITH ACCURATE MODULE COUNT
                actual_module_count = len(modules)
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #2E86AB 0%, #A23B72 100%); padding: 30px; border-radius: 15px; margin-bottom: 30px; text-align: center;">
                    <h1 style="color: white; margin: 0; font-size: 2.5rem;">{selected_path}</h1>
                    <p style="color: white; font-size: 1.2rem; margin: 10px 0; opacity: 0.9;">{path_info['description']}</p>
                    <div style="display: flex; justify-content: center; gap: 30px; margin-top: 20px;">
                        <span style="color: white; background: rgba(255,255,255,0.2); padding: 8px 16px; border-radius: 20px;">📚 {actual_module_count} Modules</span>
                        <span style="color: white; background: rgba(255,255,255,0.2); padding: 8px 16px; border-radius: 20px;">⏱️ {path_info['estimated_time']}</span>
                        <span style="color: white; background: rgba(255,255,255,0.2); padding: 8px 16px; border-radius: 20px;">📈 {path_info['difficulty']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Learning Analytics (Coursera style)
                st.markdown("### 📊 Learning Analytics")
                col1, col2, col3, col4 = st.columns(4)
                
                # Calculate analytics data
                total_lessons = sum(len(module_info['sources']) for module_info in modules.values())
                completed_lessons = len([l for l in st.session_state.completed_modules if 'lesson' in l])
                
                with col1:
                    total_modules_count = len(modules)
                    st.metric("Modules Completed", f"{len([m for m in st.session_state.completed_modules if 'Module' in m])}/{total_modules_count}")
                
                with col2:
                    st.metric("Lessons Completed", f"{completed_lessons}/{total_lessons}")
                
                with col3:
                    study_time = completed_lessons * 15  # 15 minutes per lesson
                    st.metric("Study Time", f"{study_time} min")
                
                with col4:
                    if completed_lessons == total_lessons:
                        st.metric("Certificate", "🎓 Ready!")
                    else:
                        progress_pct = (completed_lessons / total_lessons) * 100 if total_lessons > 0 else 0
                        st.metric("Progress", f"{progress_pct:.1f}%")
                
                # Learning Modules (Khan Academy style with progress)
                st.markdown("### 📚 Course Modules")
                
                # Display modules with progress tracking - SHOW ALL MODULES EVEN IF NO SOURCES
                for module_id, module_info in modules.items():
                    # Always show the module, even if no sources
                    if len(module_info['sources']) == 0:
                        # Show module with placeholder message
                        is_completed = module_id in st.session_state.completed_modules
                        completion_status = "✅ Completed" if is_completed else "📖 In Progress"
                        
                        with st.expander(f"{module_id} - {completion_status} (No sources available)", expanded=not is_completed):
                            st.markdown(f"**{module_info['description']}**")
                            st.markdown("**Learning Objectives:**")
                            for obj in module_info['learning_objectives']:
                                st.markdown(f"• {obj}")
                            st.info("No sources available for this module in the current learning path. Try selecting a different learning path from the sidebar.")
                    else:
                        # Check if module is completed
                        is_completed = module_id in st.session_state.completed_modules
                        completion_status = "✅ Completed" if is_completed else "📖 In Progress"
                        
                        with st.expander(f"{module_id} - {completion_status} ({len(module_info['sources'])} lessons)", expanded=not is_completed):
                            # Module description and objectives
                            st.markdown(f"**{module_info['description']}**")
                            st.markdown("**Learning Objectives:**")
                            for obj in module_info['learning_objectives']:
                                st.markdown(f"• {obj}")
                            
                            st.markdown("---")
                            
                            # Individual lessons (sources)
                            for idx, (_, source) in enumerate(module_info['sources'].iterrows(), 1):
                                lesson_id = f"{module_id}_lesson_{idx}"
                                is_lesson_completed = lesson_id in st.session_state.completed_modules
                                
                                # Lesson card with completion status
                                completion_icon = "✅" if is_lesson_completed else "📄"
                                st.markdown(f"""
                                <div style="background-color: {'#e8f5e8' if is_lesson_completed else '#f8f9fa'}; padding: 20px; border-radius: 10px; margin: 10px 0; border-left: 4px solid {'#4caf50' if is_lesson_completed else '#007bff'};">
                                    <h4 style="margin: 0 0 10px 0; color: #333;">{completion_icon} Lesson {idx}: {source['Title']}</h4>
                                    <p style="margin: 5px 0; color: #666;"><strong>Type:</strong> {source['Type']}</p>
                                    <p style="margin: 5px 0; color: #666;"><strong>Relevance:</strong> {source['Relevance']}</p>
                                    <p style="margin: 10px 0; color: #555;">{source['Notes']}</p>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Lesson actions
                                col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
                                
                                with col1:
                                    if pd.notna(source['URL']) and source['URL'] != '':
                                        st.link_button("📖 Read", source['URL'])
                                
                                with col2:
                                    if st.button("💡 Study", key=f"study_{lesson_id}"):
                                        # Store study result in session state
                                        study_question = f"Create a comprehensive study guide for: {source['Title']}"
                                        with st.spinner("Generating study content..."):
                                            try:
                                                study_result = st.session_state.rag_system.query(study_question)
                                                if "error" not in study_result:
                                                    st.session_state[f"study_result_{lesson_id}"] = study_result['answer']
                                                    st.rerun()
                                                else:
                                                    st.session_state[f"study_result_{lesson_id}"] = f"❌ Error generating study guide: {study_result['error']}"
                                                    st.rerun()
                                            except Exception as e:
                                                st.session_state[f"study_result_{lesson_id}"] = f"❌ Error: {str(e)}. Please try again."
                                                st.rerun()
                                
                                with col3:
                                    if st.button("🧠 Quiz", key=f"quiz_{lesson_id}"):
                                        # Store quiz result in session state
                                        quiz_question = f"Create 3 quiz questions to test understanding of: {source['Title']}"
                                        with st.spinner("Generating quiz..."):
                                            try:
                                                quiz_result = st.session_state.rag_system.query(quiz_question)
                                                if "error" not in quiz_result:
                                                    st.session_state[f"quiz_result_{lesson_id}"] = quiz_result['answer']
                                                    st.rerun()
                                                else:
                                                    st.session_state[f"quiz_result_{lesson_id}"] = f"❌ Error generating quiz: {quiz_result['error']}"
                                                    st.rerun()
                                            except Exception as e:
                                                st.session_state[f"quiz_result_{lesson_id}"] = f"❌ Error: {str(e)}. Please try again."
                                                st.rerun()
                                
                                with col4:
                                    if not is_lesson_completed:
                                        if st.button("✅ Complete", key=f"complete_{lesson_id}"):
                                            st.session_state.completed_modules.add(lesson_id)
                                            st.session_state.completed_modules.add(module_id)
                                            st.success(f"✅ Lesson {idx} completed!")
                                            st.rerun()
                                    else:
                                        st.success("✅ Completed")
                                
                                # Display study/quiz results in full-width boxes below buttons
                                if f"study_result_{lesson_id}" in st.session_state:
                                    st.markdown("**📚 Study Guide:**")
                                    st.markdown(f"""
                                    <div style="background-color: #e3f2fd; padding: 20px; border-radius: 10px; margin: 10px 0; border-left: 4px solid #2196f3; width: 100%;">
                                        {st.session_state[f"study_result_{lesson_id}"]}
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                if f"quiz_result_{lesson_id}" in st.session_state:
                                    st.markdown("**🧠 Knowledge Check:**")
                                    st.markdown(f"""
                                    <div style="background-color: #fff3cd; padding: 20px; border-radius: 10px; margin: 10px 0; border-left: 4px solid #ffc107; width: 100%;">
                                        {st.session_state[f"quiz_result_{lesson_id}"]}
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                st.markdown("---")
                
                # Next Steps and Recommendations
                if completed_lessons > 0:
                    st.markdown("### 🚀 Next Steps")
                    if completed_lessons < total_lessons:
                        st.markdown("""
                        <div style="background-color: #e8f5e8; padding: 20px; border-radius: 10px; border-left: 4px solid #4caf50;">
                            <h4 style="margin: 0 0 15px 0; color: #2e7d32;">Continue Your Learning Journey</h4>
                            <ul style="margin: 0; color: #2e7d32;">
                                <li>Complete remaining lessons to earn your certificate</li>
                                <li>Apply knowledge in the <strong>Ask Coach</strong> tab</li>
                                <li>Practice with the <strong>BMR Calculator</strong></li>
                                <li>Explore other learning paths to expand your expertise</li>
                            </ul>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <div style="background-color: #fff3cd; padding: 20px; border-radius: 10px; border-left: 4px solid #ffc107;">
                            <h4 style="margin: 0 0 15px 0; color: #856404;">🎓 Congratulations! Learning Path Complete</h4>
                            <p style="margin: 0; color: #856404;">You've successfully completed this learning path! Ready to apply your knowledge?</p>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                # Welcome screen (Khan Academy style)
                st.markdown("""
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px; border-radius: 15px; text-align: center; margin-bottom: 30px;">
                    <h1 style="color: white; margin: 0; font-size: 3rem;">🎓 Welcome to Your Learning Portal</h1>
                    <p style="color: white; font-size: 1.3rem; margin: 20px 0; opacity: 0.9;">Master evidence-based fitness and nutrition science</p>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("### 🎯 Choose Your Learning Path")
                st.markdown("Select a learning path from the sidebar to begin your personalized journey through evidence-based fitness and nutrition science.")
                
                # Feature highlights
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown("""
                    <div style="text-align: center; padding: 20px;">
                        <h3>🔬 Evidence-Based</h3>
                        <p>Learn from 23+ curated academic papers, expert interviews, and official guidelines</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown("""
                    <div style="text-align: center; padding: 20px;">
                        <h3>🎯 Structured Learning</h3>
                        <p>Follow organized modules with clear objectives and progress tracking</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    st.markdown("""
                    <div style="text-align: center; padding: 20px;">
                        <h3>🤖 AI-Powered</h3>
                        <p>Get personalized study guides, quizzes, and explanations using advanced AI</p>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("👈 Loading learning corpus...")
        
    
    with tab2:
        st.markdown('<h2 class="sub-header">Ask FitScience Coach</h2>', unsafe_allow_html=True)
        st.markdown("Ask questions about training, nutrition, supplements, or health. Get evidence-based answers with citations.")
        
        # Query input with form for Enter key support
        with st.form("ask_coach_form"):
            # Initialize default question from session state if available
            default_question = st.session_state.get('selected_quick_question', '')
            question = st.text_area(
                "Your Question:",
                value=default_question,
                placeholder="e.g., How much protein should I eat for muscle building?",
                height=100,
                key="ask_coach_question"
            )
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                ask_button = st.form_submit_button("🤖 Ask Coach", type="primary", use_container_width=True)
        
        # Process the question if button was clicked or Enter was pressed
        if ask_button and question.strip():
            # Clear the selected question after form submission
            if 'selected_quick_question' in st.session_state:
                del st.session_state.selected_quick_question
            
            with st.spinner("🔍 Searching knowledge base..."):
                result = st.session_state.rag_system.query(question.strip())
            
            if "error" not in result:
                # Display answer with green styling
                st.markdown("**💡 Answer:**")
                clean_answer = result['answer'].replace('</div>', '').replace('<div>', '').strip()
                st.markdown(f"""
                <div style="background-color: #e8f5e8; padding: 15px; border-radius: 10px; border-left: 4px solid #28a745; margin: 10px 0;">
                    {clean_answer}
                </div>
                """, unsafe_allow_html=True)
                
                # Display sources
                if result['sources']:
                    st.markdown("**📚 Sources:**")
                    for i, source in enumerate(result['sources'], 1):
                        with st.expander(f"{i}. {source['title']}"):
                            col1, col2 = st.columns([2, 1])
                            with col1:
                                st.markdown(f"**Type:** {source['type']}")
                                st.markdown(f"**Relevance:** {source['relevance']}")
                                if source['url']:
                                    st.markdown(f"**URL:** {source['url']}")
                            with col2:
                                if source['url']:
                                    st.link_button("🔗 Open Source", source['url'])
                            st.markdown("**Preview:**")
                            st.markdown(source['content_preview'])
                
                # Save to history
                st.session_state.query_history.append({
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'question': question.strip(),
                    'answer': result['answer'],
                    'sources': result['sources']
                })
                
            else:
                st.error(f"❌ Error: {result['error']}")
        
        # Quick question buttons
        st.markdown("**💡 Quick Questions:**")
        quick_questions = [
            "How much protein should I eat daily?",
            "What is progressive overload in training?",
            "What supplements are evidence-based?",
            "How much sleep do I need for recovery?",
            "What's the best workout split for beginners?",
            "How do I calculate my daily calorie needs?"
        ]
        
        col1, col2, col3 = st.columns(3)
        for i, q in enumerate(quick_questions):
            col = [col1, col2, col3][i % 3]
            with col:
                if st.button(f"❓ {q[:25]}...", key=f"quick_ask_{i}"):
                    # Store the selected question in session state
                    st.session_state.selected_quick_question = q
        
        
    
    with tab3:
        st.markdown('<h2 class="sub-header">🧮 BMR & NEAT Calculator</h2>', unsafe_allow_html=True)
        st.markdown("Calculate your Basal Metabolic Rate (BMR) and Total Daily Energy Expenditure (TDEE) with activity levels.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📏 Basic Information")
            
            # Gender
            gender = st.radio("Gender:", ["Male", "Female"], horizontal=True, key="bmr_gender_radio")
            
            # Age
            age = st.number_input("Age (years):", min_value=1, max_value=120, key="bmr_age_input")
            
            # Weight
            weight_unit = st.radio("Weight unit:", ["kg", "lbs"], horizontal=True, key="bmr_weight_unit_radio")
            if weight_unit == "kg":
                weight = st.number_input("Weight:", min_value=20.0, max_value=300.0, step=0.1, key="bmr_weight_kg_input")
            else:
                weight_lbs = st.number_input("Weight:", min_value=44.0, max_value=660.0, step=0.1, key="bmr_weight_lbs_input")
                weight = weight_lbs * 0.453592  # Convert to kg
            
            # Height
            height_unit = st.radio("Height unit:", ["cm", "ft/inches"], horizontal=True, key="bmr_height_unit_radio")
            if height_unit == "cm":
                height = st.number_input("Height:", min_value=100.0, max_value=250.0, step=0.1, key="bmr_height_cm_input")
            else:
                col_ft, col_in = st.columns(2)
                with col_ft:
                    feet = st.number_input("Feet:", min_value=3, max_value=8, key="bmr_height_ft_input")
                with col_in:
                    inches = st.number_input("Inches:", min_value=0, max_value=11, key="bmr_height_in_input")
                height = (feet * 12 + inches) * 2.54  # Convert to cm
        
        with col2:
            st.subheader("🏃‍♂️ Activity Level")
            
            # Activity level selectbox (outside form for immediate updates)
            activity_level = st.selectbox(
                "Activity Level:",
                [
                    "Sedentary",
                    "Lightly Active", 
                    "Moderately Active",
                    "Very Active",
                    "Extremely Active"
                ],
                key="bmr_activity_level_selectbox"
            )
            
            # Activity level descriptions
            activity_descriptions = {
                "Sedentary": "Little or no exercise, desk job (1.2x BMR)",
                "Lightly Active": "Light exercise 1-3 days/week (1.375x BMR)",
                "Moderately Active": "Moderate exercise 3-5 days/week (1.55x BMR)",
                "Very Active": "Hard exercise 6-7 days/week (1.725x BMR)",
                "Extremely Active": "Very hard exercise + physical job (1.9x BMR)"
            }
            
            # Display dynamic description (updates immediately)
            selected_description = activity_descriptions[activity_level]
            st.markdown(f"""
            <div style="background-color: #e3f2fd; padding: 10px; border-radius: 5px; border-left: 4px solid #2196f3; margin: 10px 0;">
                <strong>{selected_description}</strong>
            </div>
            """, unsafe_allow_html=True)
            
            # NEAT estimation
            st.subheader("🚶‍♀️ NEAT Estimation")
            neat_level = st.selectbox(
                "Daily NEAT (Non-Exercise Activity):",
                ["Low", "Moderate", "High"],
                key="bmr_neat_level_selectbox"
            )
            
            neat_descriptions = {
                "Low": "Mostly sitting, minimal daily movement (+200-400 cal)",
                "Moderate": "Some walking, light activities (+400-600 cal)", 
                "High": "Active lifestyle, lots of movement (+600-900 cal)"
            }
            
            # Display dynamic NEAT description (updates immediately)
            selected_neat_description = neat_descriptions[neat_level]
            st.markdown(f"""
            <div style="background-color: #e8f5e8; padding: 10px; border-radius: 5px; border-left: 4px solid #4caf50; margin: 10px 0;">
                <strong>{selected_neat_description}</strong>
            </div>
            """, unsafe_allow_html=True)
        
        # Calculate button (outside forms for better control)
        calculate_button = st.button("🧮 Calculate BMR & TDEE", type="primary", use_container_width=True)
        
        # Perform calculations
        if calculate_button:
            try:
                # Get values from widget session state
                gender = st.session_state.bmr_gender_radio
                age = st.session_state.bmr_age_input
                weight_unit = st.session_state.bmr_weight_unit_radio
                height_unit = st.session_state.bmr_height_unit_radio
                activity_level = st.session_state.bmr_activity_level_selectbox
                neat_level = st.session_state.bmr_neat_level_selectbox
                
                # Calculate weight in kg
                if weight_unit == "kg":
                    weight = st.session_state.bmr_weight_kg_input
                else:
                    weight = st.session_state.bmr_weight_lbs_input * 0.453592
                
                # Calculate height in cm
                if height_unit == "cm":
                    height = st.session_state.bmr_height_cm_input
                else:
                    feet = st.session_state.bmr_height_ft_input
                    inches = st.session_state.bmr_height_in_input
                    height = (feet * 12 + inches) * 2.54
                
                # Calculate BMR
                bmr = st.session_state.rag_system.calculate_bmr(weight, height, age, gender)
                
                # Calculate TDEE for selected activity level
                activity_map = {
                    "Sedentary": "sedentary",
                    "Lightly Active": "lightly_active", 
                    "Moderately Active": "moderately_active",
                    "Very Active": "very_active",
                    "Extremely Active": "extremely_active"
                }
                
                tdee = st.session_state.rag_system.calculate_tdee(bmr, activity_map[activity_level])
                
                # NEAT estimation
                neat_calories = {
                    "Low": 300,
                    "Moderate": 500,
                    "High": 750
                }
                
                total_daily = tdee + neat_calories[neat_level]
                
                # Display results
                st.markdown("---")
                st.markdown('<h3 style="color: #2E8B57;">📊 Your Results</h3>', unsafe_allow_html=True)
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("BMR", f"{bmr} cal/day", help="Calories burned at rest")
                
                with col2:
                    st.metric("TDEE", f"{tdee} cal/day", help="BMR + exercise activity")
                
                with col3:
                    st.metric("NEAT", f"+{neat_calories[neat_level]} cal/day", help="Daily non-exercise activity")
                
                with col4:
                    st.metric("Total Daily", f"{total_daily} cal/day", help="TDEE + NEAT")
                
                # Detailed breakdown
                st.markdown("### 📋 Detailed Breakdown")
                
                breakdown_data = {
                    "Component": ["BMR (Base)", "Exercise Activity", "NEAT", "**Total Daily**"],
                    "Calories": [f"{bmr}", f"{tdee - bmr}", f"+{neat_calories[neat_level]}", f"**{total_daily}**"],
                    "Percentage": [
                        f"{round((bmr/total_daily)*100, 1)}%",
                        f"{round(((tdee-bmr)/total_daily)*100, 1)}%", 
                        f"{round((neat_calories[neat_level]/total_daily)*100, 1)}%",
                        "**100%**"
                    ]
                }
                
                st.table(pd.DataFrame(breakdown_data))
                
                # Goal-based recommendations
                st.markdown("### 🎯 Goal-Based Recommendations")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("**💪 Muscle Gain**")
                    muscle_cal = total_daily + 300
                    st.metric("Target Calories", f"{muscle_cal} cal/day")
                    st.info("+300-500 cal surplus for lean gains")
                
                with col2:
                    st.markdown("**⚖️ Weight Maintenance**")
                    st.metric("Target Calories", f"{total_daily} cal/day")
                    st.info("Match your total daily expenditure")
                
                with col3:
                    st.markdown("**🔥 Fat Loss**")
                    fat_cal = total_daily - 500
                    st.metric("Target Calories", f"{fat_cal} cal/day")
                    st.info("-300-500 cal deficit for sustainable loss")
                
                # Activity level comparison
                st.markdown("### 📈 TDEE by Activity Level")
                
                activity_comparison = []
                for act_level, act_key in activity_map.items():
                    act_tdee = st.session_state.rag_system.calculate_tdee(bmr, act_key)
                    activity_comparison.append({
                        "Activity Level": act_level,
                        "TDEE": f"{act_tdee} cal/day",
                        "Difference": f"+{act_tdee - bmr} cal"
                    })
                
                st.table(pd.DataFrame(activity_comparison))
                
                # Save calculation to history
                calc_record = {
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'type': 'BMR Calculation',
                    'inputs': {
                        'age': age, 'gender': gender, 'weight_kg': round(weight, 1),
                        'height_cm': round(height, 1), 'activity': activity_level, 'neat': neat_level
                    },
                    'results': {
                        'bmr': bmr, 'tdee': tdee, 'neat': neat_calories[neat_level], 'total': total_daily
                    }
                }
                
                if 'calculation_history' not in st.session_state:
                    st.session_state.calculation_history = []
                st.session_state.calculation_history.append(calc_record)
                
            except Exception as e:
                st.error(f"❌ Calculation error: {e}")
        
        # Show calculation history
        if 'calculation_history' in st.session_state and st.session_state.calculation_history:
            st.markdown("---")
            st.markdown("### 📝 Recent Calculations")
            
            for i, calc in enumerate(reversed(st.session_state.calculation_history[-3:])):
                with st.expander(f"🕐 {calc['timestamp']} - {calc['inputs']['gender']}, {calc['inputs']['age']}yo"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**Inputs:**")
                        st.write(f"• Weight: {calc['inputs']['weight_kg']}kg")
                        st.write(f"• Height: {calc['inputs']['height_cm']}cm")
                        st.write(f"• Activity: {calc['inputs']['activity']}")
                    with col2:
                        st.markdown("**Results:**")
                        st.write(f"• BMR: {calc['results']['bmr']} cal/day")
                        st.write(f"• TDEE: {calc['results']['tdee']} cal/day")
                        st.write(f"• Total: {calc['results']['total']} cal/day")

    
    with tab4:
        st.markdown('<h2 class="sub-header">📝 Query History</h2>', unsafe_allow_html=True)
        
        if st.session_state.query_history:
            for i, entry in enumerate(reversed(st.session_state.query_history)):
                with st.expander(f"🕐 {entry['timestamp']} - {entry['question'][:50]}..."):
                    st.markdown(f"**Question:** {entry['question']}")
                    st.markdown(f"**Answer:** {entry['answer']}")
                    
                    if entry['sources']:
                        st.markdown("**Sources:**")
                        for j, source in enumerate(entry['sources'], 1):
                            st.markdown(f"{j}. {source['title']} ({source['type']})")
        else:
            st.info("No queries yet. Ask the coach some questions!")
        
        # Export history
        if st.button("📥 Export Query History"):
            history_json = json.dumps(st.session_state.query_history, indent=2)
            st.download_button(
                label="Download JSON",
                data=history_json,
                file_name=f"fitscience_queries_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

if __name__ == "__main__":
    main()
