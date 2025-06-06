# --- Imports ---
import sys
import os
import json
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer, util
import streamlit as st
import logging
import sqlite3
from datetime import datetime
from docxtpl import DocxTemplate

# Add parent directory to path for core imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Core imports
from core.cv_handler import extract_cv_text, extract_sections
from core.jd_handler import extract_jd_text
from core.file_utils import FileManager
from core.llm_client import ask_local_llm
from core.save_utils import save_cv_to_docx, save_cv_to_pdf
from core.prompt_utils import load_prompt
from core.industry_instructions import industry_instructions
from core.probability import compute_interview_probability

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Disable Streamlit's file watcher for torch modules
os.environ['STREAMLIT_WATCH_EXCLUDE'] = 'torch,torch._classes'

# Initialize FileManager
file_manager = FileManager()
logger.info(f"Initialized FileManager with base directory: {file_manager.base_dir}")
logger.info(f"Temporary directory: {file_manager.temp_dir}")
logger.info(f"Template directory: {file_manager.template_dir}")
logger.info(f"Outputs directory: {file_manager.outputs_dir}")

# Page setup
st.set_page_config(
    page_title="Operation CV",
    page_icon="🥷🏻",
    layout="wide",  # Changed to wide layout for better visibility
    initial_sidebar_state="expanded",
)

st.title("Operation CV 🥷🏻📝")
st.write("A privacy-first, local AI tool to tailor your CV to any job description.")

with st.sidebar:
    # Initialize target probability if not already set
    if 'target_prob' not in st.session_state:
        st.session_state.target_prob = 80  # Default to 80%

    # Target probability setting at the top
    st.subheader("🎯 Target Probability")
    _ = st.slider(
        "Set desired interview probability",
        min_value=0,
        max_value=100,
        value=st.session_state.target_prob,
        step=5,
        format="%d%%",
        help="Set your target interview probability. The AI will suggest improvements to reach this goal.",
        key='target_prob'
    )

    st.markdown("---")
    st.header("Settings")
    language = st.selectbox("Output Language", [
        "English (UK)", "English (US)", "French", "Spanish", "Italian"
    ])
    industry = st.selectbox(
        "Industry/Sector",
        list(industry_instructions.keys()),
        index=0
    )
    
    st.markdown("---")
    st.markdown("""
    ### 📊 Analysis & Tailoring Tool
    This tool will:
    1. Analyze your CV by section
    2. Score each section's relevance
    3. Suggest targeted improvements
    4. Help incorporate key skills and keywords
    """)
    
    st.markdown("---")
    st.caption("⚠️ Disclaimer: This tool uses AI to analyze and generate content. Always review the results carefully.")

st.subheader("Upload Files or Paste Job Description")
cv_file = st.file_uploader("Upload your CV (PDF, DOCX, or TXT)", type=["pdf", "docx", "txt"])
jd_file = st.file_uploader("Upload Job Description (PDF, DOCX, or TXT)", type=["pdf", "docx", "txt"])
jd_text_paste = st.text_area("Or paste the Job Description here", height=200)

# Function to safely extract text from files
def safe_extract_text(file_obj, file_path, is_jd=False):
    try:
        # Create temporary directory if it doesn't exist
        file_manager._ensure_directories()
        
        if file_obj.name.lower().endswith('.pdf'):
            text = extract_cv_text(file_path)
        else:
            if is_jd and not file_obj.name.lower().endswith((".pdf", ".docx", ".txt")):
                text = extract_jd_text(file_path)
            else:
                text = extract_cv_text(file_path)
        return text
    except Exception as e:
        if "No /Root object!" in str(e):
            st.error(f"The {'Job Description' if is_jd else 'CV'} file appears to be corrupted.")
        else:
            st.error(f"Error reading {'Job Description' if is_jd else 'CV'} file: {e}")
        logger.error(f"Error extracting text: {e}")
        return None

# Function to process uploaded files
def process_uploaded_file(file, is_jd=False):
    """Process an uploaded file and return its text content"""
    try:
        # Create temporary directory if it doesn't exist
        file_manager._ensure_directories()
        
        # Save the uploaded file
        temp_path = file_manager.save_uploaded_file(file, 'temp', prefix='temp_')
        
        if temp_path:
            # Extract text from the saved file
            text = safe_extract_text(file, temp_path, is_jd)
            
            try:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception as cleanup_error:
                logger.warning(f"Could not remove temporary file {temp_path}: {cleanup_error}")
            
            return text
        else:
            st.error(f"Failed to save {'job description' if is_jd else 'CV'} file")
            return None
            
    except Exception as e:
        logger.error(f"Error processing uploaded file: {e}")
        st.error(f"Error processing {'job description' if is_jd else 'CV'} file: {str(e)}")
        return None

# Function to analyze CV and JD
def analyze_documents(cv_text, jd_text):
    """Analyze CV sections and compute relevance scores against job description."""
    try:
        prob_details = compute_interview_probability(cv_text, jd_text)
        prob_before = prob_details['probability'] if isinstance(prob_details, dict) else prob_details
        st.session_state['prob_before'] = prob_before
        
        # Extract and analyze sections
        sections_dict = extract_sections(cv_text)
        section_titles_list = list(sections_dict.keys())
        section_texts = list(sections_dict.values())
        
        if not section_texts:
            return prob_details, None, sections_dict
            
        # Get semantic similarity scores for each section
        model = get_semantic_model()
        jd_emb = model.encode(jd_text, convert_to_tensor=True)
        cv_embs = model.encode(section_texts, convert_to_tensor=True)
        scores = util.pytorch_cos_sim(cv_embs, jd_emb).cpu().numpy().flatten()
        
        # Normalize scores to 0-100%
        scores = np.clip((scores + 1) * 50, 0, 100)
        
        # Create detailed analysis DataFrame
        analysis_df = pd.DataFrame({
            "Section": section_titles_list,
            "Content": section_texts,
            "Relevance": np.round(scores, 1),
            "Match_Level": ['Good match' if score >= 70 else 'Could be improved' for score in scores]
        })
        
        return prob_details, analysis_df, sections_dict
    except Exception as e:
        st.error(f"Error analyzing documents: {e}")
        return None, None, None

# Initialize semantic model
@st.cache_resource
def get_semantic_model():
    """Initialize and cache the semantic similarity model"""
    return SentenceTransformer('all-MiniLM-L6-v2')

# Initialize database and clear temporary files
def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect("operationcv.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS job_applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_title TEXT,
        company TEXT,
        industry TEXT,
        jd_text TEXT,
        cv_text TEXT,
        tailored_cv TEXT,
        prob_before REAL,
        prob_after REAL,
        created_at TEXT
    )''')
    conn.commit()
    conn.close()

# Show original CV analysis as soon as files are uploaded
if cv_file and (jd_file or jd_text_paste.strip()):
    # Extract text if not already in session state or if files have changed
    if cv_file.name != st.session_state.get('last_cv_name', ''):
        st.session_state.cv_text = process_uploaded_file(cv_file)
        st.session_state.last_cv_name = cv_file.name
        
    if jd_file and jd_file.name != st.session_state.get('last_jd_name', ''):
        st.session_state.jd_text = process_uploaded_file(jd_file, is_jd=True)
        st.session_state.last_jd_name = jd_file.name
    elif jd_text_paste.strip() != st.session_state.get('last_jd_paste', ''):
        st.session_state.jd_text = jd_text_paste
        st.session_state.last_jd_paste = jd_text_paste

    # Analyze original CV if we have valid text
    if st.session_state.cv_text and st.session_state.jd_text:
        prob_details, analysis_df, sections_dict = analyze_documents(st.session_state.cv_text, st.session_state.jd_text)
        
        if prob_details is not None:
            # Show overall results in tabs
            tab1, tab2, tab3 = st.tabs(["📊 Analysis", "📝 Section Details", "🎯 Recommendations"])
            
            with tab1:
                st.subheader("CV Analysis Overview")
                
                # Show overall probability score in a prominent container
                with st.container():
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Interview Probability", 
                                f"{int(prob_details['probability']*100)}%")
                    with col2:
                        st.metric("Skills Coverage", 
                                f"{int(prob_details['skill_coverage']*100)}%")
                    with col3:
                        st.metric("Keyword Density",
                                f"{int(prob_details['keyword_density']*100)}%")
                
                # Skills Analysis
                st.subheader("Skills Analysis")
                skills_col1, skills_col2 = st.columns(2)
                
                with skills_col1:
                    if prob_details.get('matching_skills'):
                        st.success("✅ Matching Skills")
                        for skill in prob_details['matching_skills']:
                            st.markdown(f"- {skill}")
                
                with skills_col2:
                    if prob_details.get('missing_skills'):
                        st.warning("❌ Missing Skills")
                        for skill in prob_details['missing_skills']:
                            st.markdown(f"- {skill}")
            
            with tab2:
                st.subheader("Section-by-Section Analysis")
                for _, row in analysis_df.iterrows():
                    with st.expander(f"📄 {row['Section']} - Match: {row['Relevance']}%", expanded=True):
                        # Content and Analysis in a cleaner layout
                        st.markdown("### Current Content")
                        st.text_area("", row['Content'], height=150, key=f"content_{row['Section']}")
                        
                        # Analysis and Actions
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            if row['Match_Level'] == 'Could be improved':
                                st.warning("⚠️ This section could be improved")
                            else:
                                st.success("✅ Good match with job requirements")
                        
                        with col2:
                            # Full-width button in the right column
                            if st.button("🚀 Get AI Analysis", key=f"analyze_{row['Section']}", use_container_width=True):
                                try:
                                    # Generate tailoring suggestions
                                    prompt = f"""Analyze this CV section and suggest improvements to match the job description.
                                    Keep the facts the same but rephrase to highlight relevant experience and skills.
                                    
                                    Section: {row['Section']}
                                    Current Content: {row['Content']}
                                    
                                    Job Description: {st.session_state.jd_text}
                                    """
                                    
                                    # Get suggestion from LLM and store in session state
                                    suggestion, _ = ask_local_llm(prompt, temperature=0.7)
                                    
                                    # Initialize suggestion content
                                    suggestion_content = None
                                    
                                    # Log raw suggestion for debugging
                                    logger.info(f"Raw suggestion from LLM: {suggestion}")
                                    
                                    # Handle JSON response from LLM client
                                    if isinstance(suggestion, dict) and 'sections' in suggestion:
                                        # Try to match section name case-insensitively
                                        section_lower = row['Section'].lower()
                                        for k, v in suggestion['sections'].items():
                                            if k.lower() == section_lower:
                                                suggestion_content = v
                                                logger.info(f"Found matching section '{k}' with content: {v[:100]}...")
                                                break
                                    # Handle plain text response
                                    elif isinstance(suggestion, str):
                                        suggestion_content = suggestion.strip()
                                        logger.info(f"Using plain text content: {suggestion_content[:100]}...")
                                    
                                    # Create a full-width container for suggestions
                                    st.markdown("---")
                                    st.markdown(f"### ✨ AI Suggestions for {row['Section']}")
                                    
                                    # Show versions vertically with improved spacing and visual separation
                                    st.markdown("### 📝 Current Version")
                                    st.info(row['Content'])
                                    
                                    st.markdown("---")
                                    
                                    # Display suggestion
                                    st.markdown("### ✨ Improved Version")
                                    if suggestion_content:
                                        # Clean up the suggestion if it's a string
                                        if isinstance(suggestion_content, str):
                                            suggestion_content = (suggestion_content
                                                .strip()
                                                .strip('"')  # Remove any surrounding quotes
                                                .replace('\\n', '\n')  # Handle escaped newlines
                                                .replace('\\r', '\r')  # Handle escaped carriage returns
                                                .replace('\\"', '"')   # Handle escaped quotes
                                                .replace('\\\\', '\\') # Handle escaped backslashes
                                            )
                                            
                                            logger.info(f"Final cleaned suggestion content: {suggestion_content[:100]}...")
                                        
                                        if suggestion_content.strip():
                                            # Display the cleaned suggestion
                                            st.success(suggestion_content)
                                            # Save to session state
                                            st.session_state[f'suggestion_{row["Section"]}'] = suggestion_content
                                        else:
                                            st.warning("No content available in the improved version.")
                                    else:
                                        st.warning("No suggestions available for this section.")
                                    
                                    # Add visual separation before actions
                                    st.markdown("---")
                                    
                                    # Center-align the action button
                                    col1, col2, col3 = st.columns([2, 3, 2])
                                    with col2:
                                        if st.button("📋 Copy to Clipboard", key=f"copy_{row['Section']}", use_container_width=True):
                                            st.session_state['clipboard'] = suggestion
                                            st.success("✅ Successfully copied to clipboard!")

                                except Exception as e:
                                    st.error(f"Error generating suggestions: {e}")
            
            with tab3:
                st.subheader("Recommendations")
                if prob_details['probability'] < (st.session_state.target_prob / 100):
                    st.warning(f"Your CV currently scores below your target probability of {st.session_state.target_prob}%")
                    
                    if prob_details['semantic_score'] < 0.7:
                        st.markdown("""
                        ### 📈 Content Matching
                        - Use more industry-specific terminology
                        - Focus on achievements relevant to the role
                        - Mirror key phrases from the job description
                        """)
                    
                    if prob_details['skill_coverage'] < 0.7:
                        st.markdown("""
                        ### 🎯 Skill Coverage
                        - Add missing key skills where you have experience
                        - Provide specific examples of using these skills
                        - Consider additional training in critical areas
                        """)
                    
                    if prob_details['keyword_density'] < 0.6:
                        st.markdown("""
                        ### 🔑 Keyword Optimization
                        - Naturally incorporate key terms
                        - Use variations of important keywords
                        - Ensure skills are mentioned with context
                        """)
                else:
                    st.success(f"✨ Great job! Your CV meets or exceeds your target probability of {st.session_state.target_prob}%")

# Footer
st.markdown("---")
st.caption("Made with ❤️ using Streamlit and AI")
