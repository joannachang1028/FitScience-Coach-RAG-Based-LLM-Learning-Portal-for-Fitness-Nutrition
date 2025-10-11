"""
FitScience Coach - Streamlit Interface
Personal Learning Portal for Evidence-Based Fitness & Nutrition
"""

import streamlit as st
import pandas as pd
from rag_pipeline import FitScienceRAG
import json
from datetime import datetime
import os

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
if 'use_llama' not in st.session_state:
    st.session_state.use_llama = False
if 'current_question' not in st.session_state:
    st.session_state.current_question = ""
if 'auto_trigger' not in st.session_state:
    st.session_state.auto_trigger = False
if 'question_counter' not in st.session_state:
    st.session_state.question_counter = 0
if 'last_question' not in st.session_state:
    st.session_state.last_question = ""

@st.cache_data
def load_corpus_data():
    """Load and cache corpus data"""
    try:
        df = pd.read_csv("learning_corpus.csv")
        return df
    except Exception as e:
        st.error(f"Error loading corpus: {e}")
        return None

def initialize_rag_system():
    """Initialize the RAG system"""
    if st.session_state.rag_system is None:
        with st.spinner("🚀 Initializing FitScience Coach..."):
            rag = FitScienceRAG(use_llama=st.session_state.use_llama)
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
        st.header("📚 Learning Corpus")
        
        # LLM Settings
        st.subheader("🔑 LLM Settings")
        
        # LLM Settings - Only Llama 3.2 1B via Ollama (free & local)
        st.info("🦙 Using Llama 3.2 1B via Ollama (local & free)")
        st.markdown("**Setup Instructions:**")
        st.code("""
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull Llama 3.2 1B model
ollama pull llama3.2:1b

# Start Ollama service
ollama serve
        """, language="bash")
        
        use_llama = True
        st.session_state.openai_api_key = ""  # Clear any OpenAI key
        
        if st.button("Apply Settings"):
            st.session_state.rag_system = None  # force re-init
            st.session_state.use_llama = use_llama
            st.rerun()
        
        if st.session_state.corpus_data is not None:
            # Corpus statistics
            total_sources = len(st.session_state.corpus_data)
            academic_papers = len(st.session_state.corpus_data[st.session_state.corpus_data['Type'] == 'Academic Paper'])
            podcasts = len(st.session_state.corpus_data[st.session_state.corpus_data['Type'] == 'Podcast'])
            government_resources = len(st.session_state.corpus_data[st.session_state.corpus_data['Type'] == 'Government Resource'])
            
            st.metric("Total Sources", total_sources)
            st.metric("Academic Papers", academic_papers)
            st.metric("Podcasts", podcasts)
            st.metric("Government Resources", government_resources)
            
            # Source type breakdown
            st.subheader("📊 Source Types")
            type_counts = st.session_state.corpus_data['Type'].value_counts()
            st.bar_chart(type_counts)
            
            # High relevance sources
            st.subheader("⭐ High Relevance Sources")
            high_rel = st.session_state.corpus_data[st.session_state.corpus_data['Relevance'].str.contains('High', na=False)]
            for _, row in high_rel.head(5).iterrows():
                st.markdown(f"• **{row['Title'][:50]}...**")
                st.markdown(f"  *{row['Type']}*")
    
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
            
            # Learning Dashboard Sidebar (inspired by Khan Academy/Coursera)
            with st.sidebar:
                st.markdown("### 📊 Learning Dashboard")
                
                # Overall Progress
                total_modules = 3  # Based on source types
                completed_count = len(st.session_state.completed_modules)
                overall_progress = (completed_count / total_modules) * 100
                
                st.metric("Overall Progress", f"{overall_progress:.1f}%")
                st.progress(overall_progress / 100)
                
                st.markdown("### 🎯 Course Modules")
                
                # Define modules based on source types
                module_info = {
                    "📄 Academic Papers": {
                        "description": "Evidence-based research and scientific studies",
                        "count": len(st.session_state.corpus_data[st.session_state.corpus_data['Type'] == 'Academic Paper']),
                        "icon": "📄"
                    },
                    "🎙️ Expert Podcasts": {
                        "description": "Expert interviews and practical insights",
                        "count": len(st.session_state.corpus_data[st.session_state.corpus_data['Type'] == 'Podcast']),
                        "icon": "🎙️"
                    },
                    "🏛️ Government Resources": {
                        "description": "Official guidelines and practical tools",
                        "count": len(st.session_state.corpus_data[st.session_state.corpus_data['Type'] == 'Government Resource']),
                        "icon": "🏛️"
                    }
                }
                
                for module_name, info in module_info.items():
                    st.markdown(f"**{info['icon']} {module_name}**")
                    st.markdown(f"📚 {info['count']} courses")
                    st.markdown(f"{info['description']}")
                    st.markdown("---")
        
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            ask_button = st.button("🔍 Ask Coach", type="primary")
        with col2:
            clear_button = st.button("🗑️ Clear")
        
        if clear_button:
            question = ""
            st.session_state.current_question = ""
            st.rerun()
        
        # Process query (either from Ask button or auto-trigger from quick questions)
        auto_trigger = st.session_state.get('auto_trigger', False)
        if (ask_button and question) or (auto_trigger and question):
            # Clear any previous answer to force fresh query
            if 'last_question' in st.session_state and st.session_state.last_question != question:
                # Question changed, clear previous results
                pass
            st.session_state.last_question = question
            with st.spinner("🔍 Searching knowledge base..."):
                result = st.session_state.rag_system.query(question)
            
            if "error" not in result:
                # Display answer with green styling
                st.markdown("**💡 Answer:**")
                # Apply green background styling to answer area
                # Clean the answer text to remove any HTML tags that might interfere
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
                    'question': question,
                    'answer': result['answer'],
                    'sources': result['sources']
                })
                
                # Clear auto-trigger and current question after processing
                st.session_state.auto_trigger = False
                st.session_state.current_question = ""
                
            else:
                st.error(f"❌ Error: {result['error']}")
        
        # Quick question buttons
        st.markdown("**💡 Quick Questions:**")
        col1, col2, col3 = st.columns(3)
        
        quick_questions = [
            "How much protein should I eat daily?",
            "What is progressive overload in training?",
            "What supplements are evidence-based?",
            "How much sleep do I need for recovery?",
            "What's the best workout split for beginners?",
            "How do I calculate my daily calorie needs?"
        ]
        
        for i, q in enumerate(quick_questions):
            col = [col1, col2, col3][i % 3]
            with col:
                if st.button(f"❓ {q[:25]}...", key=f"quick_{i}"):
                    st.session_state.current_question = q
                    st.session_state.auto_trigger = True  # Auto-trigger the query
                    st.session_state.question_counter = st.session_state.get('question_counter', 0) + 1
                    st.rerun()
    
    with tab2:
        st.markdown('<h2 class="sub-header">Ask FitScience Coach</h2>', unsafe_allow_html=True)
        st.markdown("Ask questions about training, nutrition, supplements, or health. Get evidence-based answers with citations.")
        
        # Query input
        default_question = st.session_state.get('current_question', '')
        question = st.text_area(
            "Your Question:",
            value=default_question,
            placeholder="e.g., How much protein should I eat for muscle building?",
            height=100,
            key=f"question_input_{st.session_state.get('question_counter', 0)}"
        )
            
            # Main Learning Interface
            st.markdown("""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px; border-radius: 15px; text-align: center; margin-bottom: 30px;">
                <h1 style="color: white; margin: 0; font-size: 3rem;">🎓 Evidence-Based Learning</h1>
                <p style="color: white; font-size: 1.3rem; margin: 20px 0; opacity: 0.9;">Master fitness and nutrition through curated research</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Learning Analytics (Coursera style) - MOVED ABOVE MODULES
            st.markdown("### 📊 Learning Analytics")
            col1, col2, col3, col4 = st.columns(4)
            
            # Calculate analytics data
            academic_count = len(st.session_state.corpus_data[st.session_state.corpus_data['Type'] == 'Academic Paper'])
            podcast_count = len(st.session_state.corpus_data[st.session_state.corpus_data['Type'] == 'Podcast'])
            gov_count = len(st.session_state.corpus_data[st.session_state.corpus_data['Type'] == 'Government Resource'])
            total_sources = academic_count + podcast_count + gov_count
            
            with col1:
                st.metric("Academic Papers", academic_count)
            
            with col2:
                st.metric("Expert Podcasts", podcast_count)
            
            with col3:
                st.metric("Government Resources", gov_count)
            
            with col4:
                st.metric("Total Courses", total_sources)
            
            # Learning Modules (Khan Academy style with progress)
            st.markdown("### 📚 Course Modules")
            
            # Group sources into structured learning modules based on source types
            modules = {
                "📄 Module 1: Academic Papers": {
                    "description": "Evidence-based research and scientific studies",
                    "sources": st.session_state.corpus_data[st.session_state.corpus_data['Type'] == 'Academic Paper'],
                    "learning_objectives": ["Understand research methodologies", "Analyze scientific papers", "Apply evidence-based principles"]
                },
                "🎙️ Module 2: Expert Podcasts": {
                    "description": "Learn from industry experts and practitioners", 
                    "sources": st.session_state.corpus_data[st.session_state.corpus_data['Type'] == 'Podcast'],
                    "learning_objectives": ["Gain practical insights", "Learn from real-world applications", "Understand expert perspectives"]
                },
                "🏛️ Module 3: Government Resources": {
                    "description": "Apply official recommendations and tools",
                    "sources": st.session_state.corpus_data[st.session_state.corpus_data['Type'] == 'Government Resource'],
                    "learning_objectives": ["Understand official guidelines", "Apply practical tools", "Implement best practices"]
                }
            }
            
            # Display modules with progress tracking
            for module_id, module_info in modules.items():
                if len(module_info['sources']) > 0:
                    # Check if module is completed
                    is_completed = module_id in st.session_state.completed_modules
                    completion_status = "✅ Completed" if is_completed else "📖 In Progress"
                    
                    with st.expander(f"{module_id} - {completion_status} ({len(module_info['sources'])} courses)", expanded=not is_completed):
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
                                <h4 style="margin: 0 0 10px 0; color: #333;">{completion_icon} Course {idx}: {source['Title']}</h4>
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
                                        study_result = st.session_state.rag_system.query(study_question)
                                        if "error" not in study_result:
                                            st.session_state[f"study_result_{lesson_id}"] = study_result['answer']
                                            st.rerun()
                            
                            with col3:
                                if st.button("🧠 Quiz", key=f"quiz_{lesson_id}"):
                                    # Store quiz result in session state
                                    quiz_question = f"Create 3 quiz questions to test understanding of: {source['Title']}"
                                    with st.spinner("Generating quiz..."):
                                        quiz_result = st.session_state.rag_system.query(quiz_question)
                                        if "error" not in quiz_result:
                                            st.session_state[f"quiz_result_{lesson_id}"] = quiz_result['answer']
                                            st.rerun()
                            
                            with col4:
                                if not is_lesson_completed:
                                    if st.button("✅ Complete", key=f"complete_{lesson_id}"):
                                        st.session_state.completed_modules.add(lesson_id)
                                        st.session_state.completed_modules.add(module_id)
                                        st.success(f"✅ Course {idx} completed!")
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
            completed_lessons = len([l for l in st.session_state.completed_modules if 'lesson' in l])
            if completed_lessons > 0:
                st.markdown("### 🚀 Next Steps")
                st.markdown("""
                <div style="background-color: #e8f5e8; padding: 20px; border-radius: 10px; border-left: 4px solid #4caf50;">
                    <h4 style="margin: 0 0 15px 0; color: #2e7d32;">Continue Your Learning Journey</h4>
                    <ul style="margin: 0; color: #2e7d32;">
                        <li>Complete remaining courses to master evidence-based fitness</li>
                        <li>Apply knowledge in the <strong>Ask Coach</strong> tab</li>
                        <li>Practice with the <strong>BMR Calculator</strong></li>
                        <li>Track your progress and achievements</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("👈 Loading learning corpus...")
    
    with tab3:
        st.markdown('<h2 class="sub-header">🧮 BMR & NEAT Calculator</h2>', unsafe_allow_html=True)
        st.markdown("Calculate your Basal Metabolic Rate (BMR) and Total Daily Energy Expenditure (TDEE) with activity levels.")
        
        # Input form
        with st.form("bmr_calculator"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📏 Basic Information")
                
                # Gender
                gender = st.radio("Gender:", ["Male", "Female"], horizontal=True)
                
                # Age
                age = st.number_input("Age (years):", min_value=1, max_value=120, value=25)
                
                # Weight
                weight_unit = st.radio("Weight unit:", ["kg", "lbs"], horizontal=True)
                if weight_unit == "kg":
                    weight = st.number_input("Weight:", min_value=20.0, max_value=300.0, value=70.0, step=0.1)
                else:
                    weight_lbs = st.number_input("Weight:", min_value=44.0, max_value=660.0, value=154.0, step=0.1)
                    weight = weight_lbs * 0.453592  # Convert to kg
                
                # Height
                height_unit = st.radio("Height unit:", ["cm", "ft/inches"], horizontal=True)
                if height_unit == "cm":
                    height = st.number_input("Height:", min_value=100.0, max_value=250.0, value=175.0, step=0.1)
                else:
                    col_ft, col_in = st.columns(2)
                    with col_ft:
                        feet = st.number_input("Feet:", min_value=3, max_value=8, value=5)
                    with col_in:
                        inches = st.number_input("Inches:", min_value=0, max_value=11, value=9)
                    height = (feet * 12 + inches) * 2.54  # Convert to cm
            
            with col2:
                st.subheader("🏃‍♂️ Activity Level")
                
                activity_level = st.selectbox(
                    "Activity Level:",
                    [
                        "Sedentary",
                        "Lightly Active", 
                        "Moderately Active",
                        "Very Active",
                        "Extremely Active"
                    ]
                )
                
                # Activity level descriptions
                activity_descriptions = {
                    "Sedentary": "Little or no exercise, desk job (1.2x BMR)",
                    "Lightly Active": "Light exercise 1-3 days/week (1.375x BMR)",
                    "Moderately Active": "Moderate exercise 3-5 days/week (1.55x BMR)",
                    "Very Active": "Hard exercise 6-7 days/week (1.725x BMR)",
                    "Extremely Active": "Very hard exercise + physical job (1.9x BMR)"
                }
                
                # Display dynamic description
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
                    ["Low", "Moderate", "High"]
                )
                
                neat_descriptions = {
                    "Low": "Mostly sitting, minimal daily movement (+200-400 cal)",
                    "Moderate": "Some walking, light activities (+400-600 cal)", 
                    "High": "Active lifestyle, lots of movement (+600-900 cal)"
                }
                
                # Display dynamic NEAT description
                selected_neat_description = neat_descriptions[neat_level]
                st.markdown(f"""
                <div style="background-color: #e8f5e8; padding: 10px; border-radius: 5px; border-left: 4px solid #4caf50; margin: 10px 0;">
                    <strong>{selected_neat_description}</strong>
                </div>
                """, unsafe_allow_html=True)
            
            # Calculate button
            calculate_button = st.form_submit_button("🧮 Calculate BMR & TDEE", type="primary")
        
        # Perform calculations
        if calculate_button:
            try:
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

    with tab3:
        st.markdown('<h2 class="sub-header">Learning Goals & Objectives</h2>', unsafe_allow_html=True)
        
        # Display learning objectives
        st.markdown("""
        ### 🎯 Learning Objectives
        
        1. **Design** a weekly training plan with progression, rest, and goal alignment
        2. **Synthesize** nutrition targets (protein, carbs, fat, calories) with training goals, lifestyle, and preferences  
        3. **Identify** food choices to meet daily calorie and micronutrient needs (vitamins, minerals)
        4. **Calculate** daily calorie consumption based on body goals (fat loss, muscle gain, maintenance) using BMR and NEAT data
        
        ### ❓ Learning Questions
        
        1. How do I create a weekly workout schedule that progresses safely toward my goals?
        2. How much protein, carbs, and fats should I eat daily for my training goals?
        3. What foods should I choose to hit my daily calories and micronutrient needs?
        4. How do I calculate my daily calorie needs using BMR and activity level?
        5. How do I track NEAT and factor it into calorie planning?
        6. What's the difference between BMR and TDEE for body composition goals?
        7. How should I adjust training and nutrition when goals change?
        """)
        
        # Progress tracking (placeholder)
        st.markdown("### 📈 Your Progress")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown('<div class="metric-box">', unsafe_allow_html=True)
            st.metric("Questions Asked", len(st.session_state.query_history))
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="metric-box">', unsafe_allow_html=True)
            calc_count = len(st.session_state.calculation_history) if 'calculation_history' in st.session_state else 0
            st.metric("BMR Calculations", calc_count)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="metric-box">', unsafe_allow_html=True)
            st.metric("Learning Modules", "4")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col4:
            st.markdown('<div class="metric-box">', unsafe_allow_html=True)
            st.metric("Completion", "25%")
            st.markdown('</div>', unsafe_allow_html=True)
    
    with tab4:
        st.markdown('<h2 class="sub-header">🎓 Personal Learning Portal</h2>', unsafe_allow_html=True)
        
        if st.session_state.corpus_data is not None:
            # Initialize session state for learning progress
            if 'learning_progress' not in st.session_state:
                st.session_state.learning_progress = {}
            if 'completed_modules' not in st.session_state:
                st.session_state.completed_modules = set()
            if 'current_learning_path' not in st.session_state:
                st.session_state.current_learning_path = []
            
            # Learning Dashboard Sidebar (inspired by Khan Academy/Coursera)
            with st.sidebar:
                st.markdown("### 📊 Learning Dashboard")
                
                # Overall Progress
                total_modules = 18  # Approximate based on corpus structure
                completed_count = len(st.session_state.completed_modules)
                overall_progress = (completed_count / total_modules) * 100
                
                st.metric("Overall Progress", f"{overall_progress:.1f}%")
                st.progress(overall_progress / 100)
                
                st.markdown("### 🎯 Learning Paths")
                
                # Define structured learning paths (like Coursera specializations)
                learning_paths = {
                    "🏋️‍♂️ Strength Training Fundamentals": {
                        "description": "Master the science of resistance training",
                        "modules": 6,
                        "estimated_time": "3-4 hours",
                        "difficulty": "Beginner to Intermediate",
                        "topics": ["progressive overload", "resistance training", "workout split", "training", "periodization"]
                    },
                    "🥗 Sports Nutrition Mastery": {
                        "description": "Evidence-based nutrition for athletes",
                        "modules": 5,
                        "estimated_time": "2-3 hours", 
                        "difficulty": "Intermediate",
                        "topics": ["protein", "nutrition", "dietary", "micronutrient", "supplement"]
                    },
                    "🔥 Metabolic Science": {
                        "description": "Understand energy systems and metabolism",
                        "modules": 4,
                        "estimated_time": "2-3 hours",
                        "difficulty": "Intermediate to Advanced", 
                        "topics": ["BMR", "metabolic", "energy", "calorie", "NEAT"]
                    },
                    "💤 Recovery & Performance": {
                        "description": "Optimize sleep and athletic recovery",
                        "modules": 3,
                        "estimated_time": "1-2 hours",
                        "difficulty": "Beginner",
                        "topics": ["sleep", "recovery", "athletic performance"]
                    }
                }
                
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
            
            # Main Learning Interface (Khan Academy/Coursera style)
            if selected_path:
                path_info = learning_paths[selected_path]
                path_topics = path_info['topics']
                
                # Filter sources for this learning path
                path_data = st.session_state.corpus_data[
                    st.session_state.corpus_data['Title'].str.contains('|'.join(path_topics), case=False, na=False) |
                    st.session_state.corpus_data['Notes'].str.contains('|'.join(path_topics), case=False, na=False)
                ]
                
                # Learning Path Header (Coursera style)
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #2E86AB 0%, #A23B72 100%); padding: 30px; border-radius: 15px; margin-bottom: 30px; text-align: center;">
                    <h1 style="color: white; margin: 0; font-size: 2.5rem;">{selected_path}</h1>
                    <p style="color: white; font-size: 1.2rem; margin: 10px 0; opacity: 0.9;">{path_info['description']}</p>
                    <div style="display: flex; justify-content: center; gap: 30px; margin-top: 20px;">
                        <span style="color: white; background: rgba(255,255,255,0.2); padding: 8px 16px; border-radius: 20px;">📚 {path_info['modules']} Modules</span>
                        <span style="color: white; background: rgba(255,255,255,0.2); padding: 8px 16px; border-radius: 20px;">⏱️ {path_info['estimated_time']}</span>
                        <span style="color: white; background: rgba(255,255,255,0.2); padding: 8px 16px; border-radius: 20px;">📈 {path_info['difficulty']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Learning Analytics (Coursera style) - MOVED ABOVE MODULES
                st.markdown("### 📊 Learning Analytics")
                col1, col2, col3, col4 = st.columns(4)
                
                # Group sources into structured learning modules FIRST
                modules = {
                    "🔬 Module 1: Research Foundation": {
                        "description": "Build your knowledge on scientific evidence",
                        "sources": path_data[path_data['Type'] == 'Academic Paper'].head(4),
                        "learning_objectives": ["Understand research methodologies", "Analyze scientific papers", "Apply evidence-based principles"]
                    },
                    "🎙️ Module 2: Expert Insights": {
                        "description": "Learn from industry experts and practitioners", 
                        "sources": path_data[path_data['Type'] == 'Podcast'].head(3),
                        "learning_objectives": ["Gain practical insights", "Learn from real-world applications", "Understand expert perspectives"]
                    },
                    "🏛️ Module 3: Official Guidelines": {
                        "description": "Apply official recommendations and tools",
                        "sources": path_data[path_data['Type'] == 'Government Resource'].head(3),
                        "learning_objectives": ["Understand official guidelines", "Apply practical tools", "Implement best practices"]
                    }
                }
                
                # Calculate analytics data
                total_lessons = sum(len(module_info['sources']) for module_info in modules.values())
                completed_lessons = len([l for l in st.session_state.completed_modules if 'lesson' in l])
                
                with col1:
                    st.metric("Modules Completed", f"{len([m for m in st.session_state.completed_modules if 'Module' in m])}/3")
                
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
                                            study_result = st.session_state.rag_system.query(study_question)
                                            if "error" not in study_result:
                                                st.session_state[f"study_result_{lesson_id}"] = study_result['answer']
                                                st.rerun()
                                
                                with col3:
                                    if st.button("🧠 Quiz", key=f"quiz_{lesson_id}"):
                                        # Store quiz result in session state
                                        quiz_question = f"Create 3 quiz questions to test understanding of: {source['Title']}"
                                        with st.spinner("Generating quiz..."):
                                            quiz_result = st.session_state.rag_system.query(quiz_question)
                                            if "error" not in quiz_result:
                                                st.session_state[f"quiz_result_{lesson_id}"] = quiz_result['answer']
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
    
    with tab5:
        st.markdown('<h2 class="sub-header">Query History</h2>', unsafe_allow_html=True)
        
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
