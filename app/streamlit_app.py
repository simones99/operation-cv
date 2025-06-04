# --- Imports ---
import sys
import os
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer, util
import streamlit as st
import logging
from core.cv_handler import extract_cv_text, extract_sections
from core.jd_handler import extract_jd_text
from core.file_utils import FileManager
from core.llm_client import ask_local_llm
from core.save_utils import save_cv_to_docx, save_cv_to_pdf
from core.prompt_utils import load_prompt
from core.industry_instructions import industry_instructions
from core.probability import compute_interview_probability
import sqlite3
from datetime import datetime
from docxtpl import DocxTemplate

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Disable Streamlit's file watcher for torch modules
os.environ['STREAMLIT_WATCH_EXCLUDE'] = 'torch,torch._classes'

# Set up logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FileManager
file_manager = FileManager()
logger.info(f"Initialized FileManager with base directory: {file_manager.base_dir}")
logger.info(f"Temporary directory: {file_manager.temp_dir}")
logger.info(f"Template directory: {file_manager.template_dir}")
logger.info(f"Outputs directory: {file_manager.outputs_dir}")

# --- Database functions ---
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

def save_application(job_title, company, industry, jd_text, cv_text, tailored_cv, prob_before, prob_after):
    """Save a job application to the database"""
    conn = sqlite3.connect("operationcv.db")
    c = conn.cursor()
    c.execute('''INSERT INTO job_applications 
                 (job_title, company, industry, jd_text, cv_text, tailored_cv, prob_before, prob_after, created_at)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (job_title, company, industry, jd_text, cv_text, tailored_cv, prob_before, prob_after, 
               datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_applications():
    """Get all saved applications, sorted by date"""
    conn = sqlite3.connect("operationcv.db")
    c = conn.cursor()
    c.execute('''SELECT id, job_title, company, industry, prob_before, prob_after, created_at 
                 FROM job_applications ORDER BY created_at DESC''')
    rows = c.fetchall()
    conn.close()
    return rows

def get_application_by_id(app_id):
    """Get a specific application by ID"""
    conn = sqlite3.connect("operationcv.db")
    c = conn.cursor()
    c.execute('SELECT * FROM job_applications WHERE id=?', (app_id,))
    row = c.fetchone()
    conn.close()
    return row

# --- Utility functions ---
def cleanup_temp_files():
    """Clean up temporary files and directories"""
    file_manager.cleanup_temp_files()

def init_session_state():
    """Initialize or reset session state variables"""
    if 'cv_text' not in st.session_state:
        st.session_state.cv_text = None
    if 'jd_text' not in st.session_state:
        st.session_state.jd_text = None
    if 'template_path' not in st.session_state:
        st.session_state.template_path = None
    if 'last_cv_name' not in st.session_state:
        st.session_state.last_cv_name = None
    if 'last_jd_name' not in st.session_state:
        st.session_state.last_jd_name = None
    if 'last_jd_paste' not in st.session_state:
        st.session_state.last_jd_paste = None
    if 'prob_before' not in st.session_state:
        st.session_state.prob_before = None
    if 'prob_after' not in st.session_state:
        st.session_state.prob_after = None
    if 'outputs_path' not in st.session_state:
        st.session_state.outputs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'outputs'))

# --- CV processing functions ---
@st.cache_resource
def get_semantic_model():
    """Initialize and cache the semantic similarity model"""
    return SentenceTransformer('all-MiniLM-L6-v2')

def parse_cv_sections(cv_text):
    """Parse CV text into sections for template use"""
    sections_dict = extract_sections(cv_text)
    
    # Normalize section names for template use
    context = {}
    name_map = {
        'Professional Summary': 'summary',
        'Summary': 'summary',
        'Profile': 'summary',
        'Objective': 'summary',
        'Experience': 'experience',
        'Work Experience': 'experience',
        'Professional Experience': 'experience',
        'Additional Experience': 'experience',
        'Education': 'education',
        'Academic Background': 'education',
        'Skills': 'skills',
        'Technical Skills': 'skills',
        'Core Competencies': 'skills',
        'Skills & Certifications': 'skills',
        'Skills And Certifications': 'skills',
        'Projects': 'projects',
        'Publications': 'publications',
        'Languages': 'languages',
        'Interests': 'interests',
        'Awards': 'awards',
        'Activities': 'activities',
        'Volunteer': 'volunteering',
        'Volunteering': 'volunteering',
        'Extracurricular': 'extracurricular',
        'Extra Curricular': 'extracurricular',
        'Additional / Extra Curricular Experience': 'extracurricular'
    }
    
    # Map section names to template variables
    for title, content in sections_dict.items():
        normalized = title.title()  # Convert to title case for consistent matching
        template_name = name_map.get(normalized, title.lower().replace(' ', '_'))
        context[template_name] = content.strip()
    
    # Add special fields
    if 'Full CV' in sections_dict:
        # If CV wasn't split into sections, use full content for summary
        context['content'] = sections_dict['Full CV'].strip()
        
    return context

# Initialize the semantic model only once
@st.cache_resource
def get_semantic_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

# --- Database setup ---
def init_db():
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

# --- Lifecycle management ---
def cleanup_temp_files():
    """Clean up temporary files and directories"""
    file_manager.cleanup_temp_files()

def init_session_state():
    """Initialize or reset session state variables"""
    if 'cv_text' not in st.session_state:
        st.session_state.cv_text = None
    if 'jd_text' not in st.session_state:
        st.session_state.jd_text = None
    if 'template_path' not in st.session_state:
        st.session_state.template_path = None
    if 'last_cv_name' not in st.session_state:
        st.session_state.last_cv_name = None
    if 'last_jd_name' not in st.session_state:
        st.session_state.last_jd_name = None
    if 'last_jd_paste' not in st.session_state:
        st.session_state.last_jd_paste = None
    if 'prob_before' not in st.session_state:
        st.session_state.prob_before = None
    if 'prob_after' not in st.session_state:
        st.session_state.prob_after = None
    if 'outputs_path' not in st.session_state:
        st.session_state.outputs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'outputs'))

init_db()
cleanup_temp_files()
init_session_state()

# Page setup
st.set_page_config(
    page_title="Operation CV",
    page_icon="🥷🏻",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Initialize session state
def init_session_state():
    """Initialize or reset session state variables"""
    if 'cv_text' not in st.session_state:
        st.session_state.cv_text = None
    if 'jd_text' not in st.session_state:
        st.session_state.jd_text = None
    if 'template_path' not in st.session_state:
        st.session_state.template_path = None
    if 'last_cv_name' not in st.session_state:
        st.session_state.last_cv_name = None
    if 'last_jd_name' not in st.session_state:
        st.session_state.last_jd_name = None
    if 'last_jd_paste' not in st.session_state:
        st.session_state.last_jd_paste = None
    if 'prob_before' not in st.session_state:
        st.session_state.prob_before = None
    if 'prob_after' not in st.session_state:
        st.session_state.prob_after = None
    if 'outputs_path' not in st.session_state:
        st.session_state.outputs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'outputs'))
    if 'target_prob' not in st.session_state:
        st.session_state.target_prob = 0.8

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
    output_format = st.selectbox("Export Format", ["docx", "pdf"])
    industry = st.selectbox(
        "Industry/Sector",
        list(industry_instructions.keys()),
        index=0
    )
    
    # Add template uploader
    st.markdown("---")
    st.subheader("CV Template")
    st.markdown("""
    Upload a DOCX template with placeholders for CV sections. Available variables:
    - `{{ summary }}` - Professional summary/profile
    - `{{ experience }}` - Work experience
    - `{{ education }}` - Education history
    - `{{ skills }}` - Skills and competencies
    - `{{ projects }}` - Projects section
    - `{{ publications }}` - Publications section
    - `{{ languages }}` - Languages section
    - `{{ content }}` - Full CV content if not split into sections
    """)
    template_file = st.file_uploader("Upload DOCX template (optional)", type=["docx"])
    
    # Ensure directories exist
    file_manager._ensure_directories()
    
    if template_file:
        try:
            # Save template to template directory
            template_path = file_manager.save_uploaded_file(template_file, 'templates', prefix='custom_')
            st.session_state.template_path = template_path
            st.success("✅ Custom template loaded successfully!")
        except Exception as e:
            logger.error(f"Error loading template: {e}")
            st.error(f"Error loading template file: {str(e)}")
            template_path = file_manager.get_default_template()
            st.info("Using default template instead")
    else:
        # Use saved template path or fall back to default
        template_path = st.session_state.get('template_path')
        if not template_path or not os.path.exists(template_path):
            template_path = file_manager.get_default_template()
            st.info("Using default CV template")
        
    st.markdown("---")
    st.caption("⚠️ Disclaimer: This tool uses AI to analyze and generate content. Always review the results carefully as AI-generated content may contain inaccuracies or errors.")

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
            st.error(f"The {'Job Description' if is_jd else 'CV'} file appears to be an invalid or corrupted PDF. Please try converting it to a different format (DOCX or TXT) or upload a different file.")
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
        # Extract probability value from details dictionary
        prob_before = prob_details['probability'] if isinstance(prob_details, dict) else prob_details
        st.session_state['prob_before'] = prob_before
        
        sections_dict = extract_sections(cv_text)
        section_titles_list = list(sections_dict.keys())
        section_texts = list(sections_dict.values())
        
        # Skip analysis if no sections found
        if not section_texts:
            return prob_details, None, sections_dict
            
        model = get_semantic_model()
        jd_emb = model.encode(jd_text, convert_to_tensor=True)
        cv_embs = model.encode(section_texts, convert_to_tensor=True)
        scores = util.pytorch_cos_sim(cv_embs, jd_emb).cpu().numpy().flatten()
        
        # Normalize scores to 0-100%
        scores = np.clip((scores + 1) * 50, 0, 100)
        
        original_df = pd.DataFrame({
            "Section Title": section_titles_list,
            "Score": np.round(scores, 1)
        }).sort_values("Score", ascending=False)
        
        return prob_before, original_df, sections_dict
    except Exception as e:
        st.error(f"Error analyzing documents: {e}")
        return None, None, None

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
        prob_before, original_df, sections_dict = analyze_documents(st.session_state.cv_text, st.session_state.jd_text)
        
        if prob_before is not None:
            st.subheader("Original CV Analysis")
            
            # Explanation of scoring
            with st.expander("ℹ️ How scores are calculated", expanded=False):
                st.markdown("""
                ### Section Relevance Scores
                Each section of your CV is analyzed for relevance to the job description using semantic similarity:
                - **90-100%**: Exceptional match - Section is highly relevant
                - **70-89%**: Strong match - Good alignment with job requirements
                - **50-69%**: Moderate match - Some relevant content
                - **Below 50%**: Low match - Consider revising or emphasizing different points
                
                The interview probability is calculated based on:
                - Semantic similarity between CV and job description
                - Keyword matching for skills and requirements
                - Industry-specific scoring adjustments
                """)
            
            col1, col2 = st.columns([2, 1])
            with col1:
                if original_df is not None:
                    # Create a bar chart with custom formatting
                    chart_data = original_df.copy()
                    chart_data = chart_data.sort_values("Score", ascending=True)
                    
                    # Add color coding based on scores
                    colors = ['#ff4b4b' if x < 50 else '#faa356' if x < 70 
                            else '#4bd27c' if x < 90 else '#2ea043' 
                            for x in chart_data.Score]
                            
                    st.write("Section Relevance:")
                    st.bar_chart(
                        data=chart_data.set_index("Section Title"),
                        use_container_width=True
                    )
            
            with col2:
                # Get probability value safely
                prob_value = prob_before['probability'] if isinstance(prob_before, dict) else prob_before
                metric_color = '#ff4b4b' if prob_value < 0.5 else '#faa356' if prob_value < 0.7 else '#2ea043'
                st.markdown(f"""
                <div style='background-color: {metric_color}20; padding: 1rem; border-radius: 0.5rem;'>
                    <h3 style='color: {metric_color}; margin:0;'>
                        {int(prob_before*100)}%
                    </h3>
                    <p style='margin:0; color: {metric_color};'>Interview Probability</p>
                </div>
                """, unsafe_allow_html=True)
                
                if prob_before < 0.5:
                    st.warning("⚠️ Low match - Consider significant revisions")
                elif prob_before < 0.7:
                    st.info("📝 Moderate match - Some tailoring recommended")
                else:
                    st.success("✅ Strong match - Minor optimizations may help")
                    
                if len(sections_dict) < 3:
                    st.warning("Your CV was split into fewer than 3 sections. Consider adjusting your section headers for better analysis.")

# Tailor CV button and processing
if st.button("Tailor My CV"):
    if not cv_file or (not jd_file and not jd_text_paste.strip()):
        st.error("Please upload a CV and either upload or paste a Job Description.")
    elif not st.session_state.cv_text or not st.session_state.jd_text:
        st.error("Please ensure both CV and Job Description are properly loaded.")
    else:
        try:
            # Initialize progress
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Load system prompt
            status_text.text("Loading prompts and instructions...")
            progress_bar.progress(10)
            
            system_prompt = load_prompt("prompts/cv_tailor_system.txt")
            industry_instruction = industry_instructions.get(industry, "")
            user_prompt = f"""
            Below is a job description and a base CV. 
            Rewrite the CV so it is tailored to the job, emphasizing relevant skills, experience, and tone. Only output the tailored CV.\n\n
            Job Description:\n{st.session_state.jd_text}\n\n
            Base CV:\n{st.session_state.cv_text}\n\n
            Please write the tailored CV in {language}.\n\n
            Industry/Sector: {industry}\n
            Instructions for this industry: {industry_instruction}\n"""

            # Generate tailored CV
            status_text.text("Generating tailored CV with AI model...")
            progress_bar.progress(30)
            
            # Get JSON response from LLM
            cv_json_response, messages = ask_local_llm(
                user_prompt, 
                system_prompt=system_prompt,
                use_schema=True
            )

            if isinstance(cv_json_response, str) and cv_json_response.startswith("Error"):
                progress_bar.empty()
                status_text.empty()
                st.error(cv_json_response)
                st.stop()

            try:
                # Parse JSON response if it's a string
                if isinstance(cv_json_response, str):
                    cv_data = json.loads(cv_json_response)
                else:
                    cv_data = cv_json_response

                # Convert JSON structure to formatted CV text
                sections = cv_data.get('sections', {})
                cv_parts = []

                # Add summary
                if 'summary' in sections:
                    cv_parts.append("PROFESSIONAL SUMMARY")
                    cv_parts.append(sections['summary'])
                    cv_parts.append("")

                # Add experience
                if 'experience' in sections and sections['experience']:
                    cv_parts.append("EXPERIENCE")
                    for exp in sections['experience']:
                        cv_parts.append(f"{exp['title']} | {exp['company']}")
                        cv_parts.append(exp['period'])
                        for desc in exp['description']:
                            cv_parts.append(f"• {desc}")
                        cv_parts.append("")

                # Add education
                if 'education' in sections and sections['education']:
                    cv_parts.append("EDUCATION")
                    for edu in sections['education']:
                        cv_parts.append(f"{edu['degree']} | {edu['institution']}")
                        cv_parts.append(edu['period'])
                        if 'details' in edu and edu['details']:
                            for detail in edu['details']:
                                cv_parts.append(f"• {detail}")
                        cv_parts.append("")

                # Add skills
                if 'skills' in sections:
                    cv_parts.append("SKILLS")
                    if 'technical' in sections['skills']:
                        cv_parts.append("Technical: " + ", ".join(sections['skills']['technical']))
                    if 'soft' in sections['skills']:
                        cv_parts.append("Soft Skills: " + ", ".join(sections['skills']['soft']))
                    cv_parts.append("")

                # Add projects
                if 'projects' in sections and sections['projects']:
                    cv_parts.append("PROJECTS")
                    for proj in sections['projects']:
                        cv_parts.append(proj['name'])
                        for desc in proj['description']:
                            cv_parts.append(f"• {desc}")
                        cv_parts.append("")

                # Add publications
                if 'publications' in sections and sections['publications']:
                    cv_parts.append("PUBLICATIONS")
                    for pub in sections['publications']:
                        cv_parts.append(f"• {pub}")
                    cv_parts.append("")

                # Add languages
                if 'languages' in sections and sections['languages']:
                    cv_parts.append("LANGUAGES")
                    lang_parts = [f"{lang['language']} ({lang['level']})" for lang in sections['languages']]
                    cv_parts.append(", ".join(lang_parts))
                    cv_parts.append("")

                # Join all parts with proper spacing
                tailored_cv = "\n".join(cv_parts).strip()

                if not tailored_cv:
                    progress_bar.empty()
                    status_text.empty()
                    st.error("Failed to generate CV content. Please try again.")
                    st.stop()

            except Exception as e:
                progress_bar.empty()
                status_text.empty()
                st.error(f"Error processing CV data: {str(e)}")
                st.stop()
                
            progress_bar.progress(50)
            status_text.text("Analyzing tailored CV...")

            # Analyze tailored CV
            prob_details = compute_interview_probability(tailored_cv, st.session_state.jd_text)
            prob_after = prob_details['probability']
            st.session_state['prob_after'] = prob_after
            
            # Calculate the gap to target (convert target from percentage to decimal)
            target_prob_decimal = st.session_state.target_prob / 100.0
            prob_gap = target_prob_decimal - prob_after
            
            # Display analysis and suggestions
            analysis_col1, analysis_col2 = st.columns([2, 1])
            
            with analysis_col1:
                st.subheader("CV Analysis & Suggestions")
                
                # Show probability metrics
                metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
                with metrics_col1:
                    current_score = int(prob_after * 100)
                    score_change = int((prob_after - st.session_state['prob_before']) * 100)
                    st.metric("Current Score", 
                             f"{current_score}%",
                             f"{score_change:+d}%" if score_change != 0 else None)
                with metrics_col2:
                    st.metric("Target Score", f"{st.session_state.target_prob}%")
                with metrics_col3:
                    gap_color = "normal" if prob_gap <= 0 else "inverse"
                    gap_value = abs(int(prob_gap * 100))
                    st.metric("Gap to Target", 
                             f"{gap_value}%",
                             "Above target" if prob_gap <= 0 else "Below target",
                             delta_color=gap_color)
                
                # Show detailed component scores
                st.markdown("### Component Scores")
                st.markdown("Each component contributes to your overall interview probability:")
                
                # Create score bars with custom styling
                components = {
                    'Content Match (50%)': prob_details['semantic_score'],
                    'Skill Coverage (30%)': prob_details['skill_coverage'],
                    'Keyword Density (20%)': prob_details['keyword_density']
                }
                
                for component, score in components.items():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.progress(score)
                    with col2:
                        st.write(f"{int(score * 100)}%")
                
                # Add explanations for the scores
                with st.expander("ℹ️ What do these scores mean?"):
                    st.markdown("""
                    - **Content Match**: How well your CV content aligns with the job description
                    - **Skill Coverage**: Percentage of required skills found in your CV
                    - **Keyword Density**: How effectively you've used relevant keywords
                    """)
                
                if prob_after < st.session_state.target_prob:
                    with st.expander("💡 Improvement Suggestions", expanded=True):
                        st.markdown("### Areas for Improvement")
                        
                        # Content suggestions based on semantic score
                        if prob_details['semantic_score'] < 0.7:
                            st.markdown("""
                            #### 📊 Content Alignment
                            - Rephrase your experience to better match the job description language
                            - Focus more on achievements that relate to the role
                            - Use industry-specific terminology from the job posting
                            """)
                        
                        # Skills suggestions
                        if prob_details['skill_coverage'] < 0.7:
                            st.markdown("#### 🎯 Missing Key Skills")
                            st.markdown("Add these skills to improve your match:")
                            for skill in prob_details['missing_skills']:
                                st.markdown(f"- {skill}")
                            st.markdown("")  # Add some spacing
                            
                            st.markdown("#### ✅ Matching Skills")
                            for skill in prob_details['matching_skills']:
                                st.markdown(f"- {skill}")
                            st.markdown("")  # Add some spacing
                        
                        # Keyword density suggestions
                        if prob_details['keyword_density'] < 0.6:
                            st.markdown("""
                            #### 🔍 Keyword Optimization
                            - Incorporate more key terms from the job description
                            - Use variations of important keywords
                            - Ensure skills are mentioned in context of achievements
                            """)
                        
                        st.markdown("""
                        ### How to Improve Your Score
                        1. Focus on the components with lowest scores first
                        2. Address the suggestions for each component
                        3. Ensure changes maintain truthfulness and relevance
                        4. Click 'Tailor My CV' to recalculate
                        """)
            
            with analysis_col2:
                # Show skill match summary
                st.markdown("### Skill Match Summary")
                matching = len(prob_details.get('matching_skills', []))
                missing = len(prob_details.get('missing_skills', []))
                extra = len(prob_details.get('extra_skills', []))
                total_required = matching + missing
                
                # Create a progress bar for skill coverage
                st.markdown(f"**Skills Coverage:** {int(prob_details['skill_coverage']*100)}%")
                st.progress(prob_details['skill_coverage'])
                
                st.markdown(f"""
                - ✅ Matching: {matching}
                - ❌ Missing: {missing}
                - ℹ️ Additional: {extra}
                """)
                
                # Show matching skills
                if prob_details.get('matching_skills'):
                    with st.expander("✅ Matching Skills"):
                        for skill in prob_details['matching_skills']:
                            st.markdown(f"- {skill}")
                            
                # Target achievement guidance
                if prob_gap > 0:
                    st.markdown("### 🎯 To Reach Target")
                    improvements_needed = []
                    if prob_details['semantic_score'] < 0.7:
                        improvements_needed.append("• Improve content matching")
                    if prob_details['skill_coverage'] < 0.7:
                        improvements_needed.append("• Add missing key skills")
                    if prob_details['keyword_density'] < 0.6:
                        improvements_needed.append("• Increase keyword usage")
                    
                    for improvement in improvements_needed:
                        st.markdown(improvement)

            # Display results as before
            st.subheader("Tailored CV Analysis")
            
            # Enhanced probability metric with color coding
            metric_color = '#ff4b4b' if prob_after < 0.5 else '#faa356' if prob_after < 0.7 else '#2ea043'
            prob_delta = int((prob_after - st.session_state['prob_before'])*100)
            st.metric(
                "Interview Probability",
                f"{int(prob_after*100)}%",
                delta=f"{prob_delta:+d}%",
                delta_color="normal"
            )
            
            # Calculate section relevance for tailored CV
            ai_sections_dict = extract_sections(tailored_cv)
            ai_section_titles = list(ai_sections_dict.keys())
            ai_section_texts = list(ai_sections_dict.values())
            
            model = get_semantic_model()
            jd_emb = model.encode(st.session_state.jd_text, convert_to_tensor=True)
            ai_cv_embs = model.encode(ai_section_texts, convert_to_tensor=True)
            ai_scores = util.pytorch_cos_sim(ai_cv_embs, jd_emb).cpu().numpy().flatten()
            
            tailored_df = pd.DataFrame({
                "Section Title": ai_section_titles,
                "Score": np.round(ai_scores, 2)
            }).sort_values("Score", ascending=False)

            progress_bar.progress(80)
            status_text.text("Preparing final results...")

            # Display tailored results
            st.subheader("Tailored CV Preview")
            st.text_area("Preview", tailored_cv, height=400)

            # Word count warning
            word_count = len(tailored_cv.split())
            if word_count > 600:
                st.warning(f"The tailored CV is likely longer than one page (word count: {word_count}). Consider revising your input or prompt.")

            # File handling information
            st.info("""
            💾 Generated files are saved in the `outputs` folder:
            - CV files are named: `tailored_cv_[originalname]_[jobname].[format]`
            - Files are cleaned up periodically but you can always regenerate them
            - Download your files using the buttons below
            """)

            # Save output using FileManager
            try:
                # Always use template (default or custom)
                if not template_path:
                    template_path = file_manager.get_default_template()
                    if not template_path:
                        st.error("No template available. Please check the template directory.")
                        st.stop()

                base_filename = f"tailored_cv_{os.path.splitext(cv_file.name)[0]}_{os.path.splitext(jd_file.name)[0] if jd_file else 'pasted_jd'}.{output_format}"
                output_path = os.path.join(file_manager.outputs_dir, base_filename)

                # Parse CV sections for template
                context = parse_cv_sections(tailored_cv)
                
                if output_format == "docx":
                    # Use template for DOCX output
                    doc = DocxTemplate(template_path)
                    doc.render(context)
                    doc.save(output_path)
                    st.success("✅ CV exported using template!")
                else:
                    # For PDF, first create DOCX then convert
                    temp_docx = os.path.join(file_manager.temp_dir, "temp.docx")
                    doc = DocxTemplate(template_path)
                    doc.render(context)
                    doc.save(temp_docx)
                    save_cv_to_pdf(tailored_cv, output_path, docx_path=temp_docx)
                    os.remove(temp_docx)

                if os.path.exists(output_path):
                    with open(output_path, "rb") as f:
                        st.download_button(
                            f"Download tailored CV as .{output_format}",
                            f,
                            file_name=os.path.basename(output_path),
                            help="Click to download your tailored CV"
                        )
            except Exception as e:
                logger.error(f"Error saving output file: {e}")
                st.error(f"Error saving output file: {str(e)}")
                if 'output_path' in locals() and os.path.exists(output_path):
                    try:
                        os.remove(output_path)
                    except Exception:
                        pass
        except Exception as e:
            logger.error(f"Error in CV processing: {e}")
            st.error(f"Error during CV processing: {str(e)}")
            # Clean up any temporary files
            file_manager.cleanup_temp_files()
            st.stop()

# --- Sidebar: View saved applications ---
with st.sidebar:
    st.markdown("---")
    st.subheader("📁 Saved Applications")
    applications = get_applications()
    if applications:
        app_options = [f"{a[1]} @ {a[2]} ({datetime.fromisoformat(a[6]).strftime('%Y-%m-%d')})" for a in applications]
        selected = st.selectbox("View previous applications", ["-"] + app_options)
        if selected != "-":
            idx = app_options.index(selected)
            app_id = applications[idx][0]
            app_data = get_application_by_id(app_id)
            with st.expander("Show Details", expanded=True):
                st.markdown(f"""
                ### {app_data[1]}
                **Company:** {app_data[2]}  
                **Industry:** {app_data[3]}  
                **Date:** {datetime.fromisoformat(app_data[9]).strftime('%Y-%m-%d %H:%M')}  
                **Success Rate:** {int(app_data[8]*100)}% (+{int((app_data[8]-app_data[7])*100)}%)
                """)
                
                tab1, tab2, tab3 = st.tabs(["📋 Job Description", "📄 Original CV", "✨ Tailored CV"])
                
                with tab1:
                    st.text_area("Job Description", app_data[4], height=200)
                with tab2:
                    st.text_area("Original CV", app_data[5], height=200)
                with tab3:
                    st.text_area("Tailored CV", app_data[6], height=200)
                    
                # Export options
                export_col1, export_col2 = st.columns(2)
                with export_col1:
                    # Re-export as DOCX
                    if st.button("Export as DOCX"):
                        try:
                            # Get template for export
                            template_path = template_path or file_manager.get_default_template()
                            if not template_path:
                                st.error("No template available. Please check the template directory.")
                                st.stop()
                                
                            export_path = os.path.join(file_manager.outputs_dir, f"{app_data[1]}_{app_data[2]}.docx")
                            context = parse_cv_sections(app_data[6])  # Use the tailored CV
                            doc = DocxTemplate(template_path)
                            doc.render(context)
                            doc.save(export_path)
                            with open(export_path, "rb") as f:
                                st.download_button(
                                    "Download DOCX",
                                    f,
                                    file_name=os.path.basename(export_path)
                                )
                        except Exception as e:
                            st.error(f"Error exporting DOCX: {e}")
                
                with export_col2:
                    # Re-export as PDF
                    if st.button("Export as PDF"):
                        try:
                            # Get template for export
                            template_path = template_path or file_manager.get_default_template()
                            if not template_path:
                                st.error("No template available. Please check the template directory.")
                                st.stop()
                                
                            # First create DOCX from template
                            temp_docx = os.path.join(file_manager.temp_dir, "temp.docx")
                            context = parse_cv_sections(app_data[6])
                            doc = DocxTemplate(template_path)
                            doc.render(context)
                            doc.save(temp_docx)
                            
                            # Convert to PDF
                            export_path = os.path.join(file_manager.outputs_dir, f"{app_data[1]}_{app_data[2]}.pdf")
                            save_cv_to_pdf(app_data[6], export_path, docx_path=temp_docx)
                            os.remove(temp_docx)
                            with open(export_path, "rb") as f:
                                st.download_button(
                                    "Download PDF",
                                    f,
                                    file_name=os.path.basename(export_path)
                                )
                        except Exception as e:
                            st.error(f"Error exporting PDF: {e}")
    else:
        st.info("No applications saved yet. Use the form after tailoring your CV to save applications.")


