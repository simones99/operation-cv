import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from core.cv_handler import extract_cv_text, extract_sections
from core.jd_handler import extract_jd_text
from core.llm_client import ask_local_llm
from core.save_utils import save_cv_to_docx, save_cv_to_pdf
from core.prompt_utils import load_prompt
from core.industry_instructions import industry_instructions
from core.probability import compute_interview_probability

st.set_page_config(page_title="CV Tailor Agent", layout="centered")
st.title("CV Tailor Agent 📝")
st.write("A privacy-first, local AI tool to tailor your CV to any job description.")

with st.sidebar:
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
    # Interview probability display (after file upload and text extraction)
    if "prob_before" in st.session_state:
        st.subheader("Interview Probability Estimate (Before Tailoring)")
        st.metric("Estimated Probability to Get Interview", f"{int(st.session_state['prob_before']*100)}%", delta=None, delta_color="inverse")
    if "prob_after" in st.session_state:
        st.subheader("Interview Probability Estimate (After Tailoring)")
        st.metric("Estimated Probability to Get Interview", f"{int(st.session_state['prob_after']*100)}%", delta=int((st.session_state['prob_after']-st.session_state['prob_before'])*100), delta_color="normal")

st.subheader("Upload Files or Paste Job Description")
cv_file = st.file_uploader("Upload your CV (PDF, DOCX, or TXT)", type=["pdf", "docx", "txt"])
jd_file = st.file_uploader("Upload Job Description (PDF, DOCX, or TXT)", type=["pdf", "docx", "txt"])
jd_text_paste = st.text_area("Or paste the Job Description here", height=200)

if st.button("Tailor My CV"):
    if not cv_file or (not jd_file and not jd_text_paste.strip()):
        st.error("Please upload a CV and either upload or paste a Job Description.")
    else:
        # Save uploaded files temporarily
        os.makedirs(".tmp", exist_ok=True)
        cv_path = f".tmp/{cv_file.name}"
        with open(cv_path, "wb") as f: f.write(cv_file.read())
        if jd_file:
            jd_path = f".tmp/{jd_file.name}"
            with open(jd_path, "wb") as f: f.write(jd_file.read())
        else:
            jd_path = None

        # Extract text with error handling
        try:
            cv_text = extract_cv_text(cv_path)
        except Exception as e:
            st.error(f"Error reading CV file: {e}")
            os.remove(cv_path)
            if jd_path: os.remove(jd_path)
            st.stop()
        if jd_file:
            try:
                jd_text = extract_cv_text(jd_path) if jd_file.name.lower().endswith((".pdf", ".docx", ".txt")) else extract_jd_text(jd_path)
            except Exception as e:
                st.error(f"Error reading Job Description file: {e}")
                os.remove(cv_path)
                os.remove(jd_path)
                st.stop()
        else:
            jd_text = jd_text_paste

        # Input validation: check for empty files/text
        if not cv_text.strip():
            st.error("The CV file appears to be empty or unreadable.")
            os.remove(cv_path)
            if jd_path: os.remove(jd_path)
            st.stop()
        if not jd_text.strip():
            st.error("The Job Description appears to be empty or unreadable.")
            os.remove(cv_path)
            if jd_path: os.remove(jd_path)
            st.stop()

        # Load system prompt
        system_prompt = load_prompt("prompts/cv_tailor_system.txt")
        industry_instruction = industry_instructions.get(industry, "")
        user_prompt = f"""
Below is a job description and a base CV. Rewrite the CV so it is tailored to the job, emphasizing relevant skills, experience, and tone. Only output the tailored CV.\n\nJob Description:\n{jd_text}\n\nBase CV:\n{cv_text}\n\nPlease write the tailored CV in {language}.\n\nIndustry/Sector: {industry}\nInstructions for this industry: {industry_instruction}\n"""

        with st.spinner("Generating tailored CV with your local AI model (this may take up to a few minutes)..."):
            try:
                tailored_cv, messages = ask_local_llm(user_prompt, system_prompt=system_prompt)
            except Exception as e:
                st.error(f"Error communicating with the local LLM: {e}")
                os.remove(cv_path)
                if jd_path: os.remove(jd_path)
                st.stop()

        # Output validation: check for empty or too long output
        if not tailored_cv or not tailored_cv.strip():
            st.error("The tailored CV output is empty. Please check your input files or try again.")
            os.remove(cv_path)
            if jd_path: os.remove(jd_path)
            st.stop()
        # Warn if output is likely over 1 page (rough estimate: >600 words)
        word_count = len(tailored_cv.split())
        if word_count > 600:
            st.warning(f"The tailored CV is likely longer than one page (word count: {word_count}). Consider revising your input or prompt.")

        st.subheader("Tailored CV Preview")
        st.text_area("Preview", tailored_cv, height=400)

        # Save output
        os.makedirs("outputs", exist_ok=True)
        base_out = f"tailored_cv_{os.path.splitext(cv_file.name)[0]}_{os.path.splitext(jd_file.name)[0] if jd_file else 'pasted_jd'}"
        out_path = os.path.join("outputs", f"{base_out}.{output_format}")
        if output_format == "docx":
            save_cv_to_docx(tailored_cv, out_path)
        else:
            save_cv_to_pdf(tailored_cv, out_path)

        with open(out_path, "rb") as f:
            st.download_button(f"Download tailored CV as .{output_format}", f, file_name=os.path.basename(out_path))

        # Clean up temp files
        os.remove(cv_path)
        if jd_path: os.remove(jd_path)

# Section scoring UI before LLM
with st.sidebar:
    st.subheader("Section Relevance Preview (Original CV)")
    if cv_file and (jd_file or jd_text_paste.strip()):
        # Save uploaded files temporarily
        os.makedirs(".tmp", exist_ok=True)
        cv_path = f".tmp/{cv_file.name}"
        with open(cv_path, "wb") as f: f.write(cv_file.read())
        if jd_file:
            jd_path = f".tmp/{jd_file.name}"
            with open(jd_path, "wb") as f: f.write(jd_file.read())
        else:
            jd_path = None
        # Extract text
        try:
            cv_text = extract_cv_text(cv_path)
        except Exception as e:
            st.error(f"Error reading CV file: {e}")
            os.remove(cv_path)
            if jd_path: os.remove(jd_path)
            st.stop()
        if jd_file:
            try:
                jd_text = extract_cv_text(jd_path) if jd_file.name.lower().endswith((".pdf", ".docx", ".txt")) else extract_jd_text(jd_path)
            except Exception as e:
                st.error(f"Error reading Job Description file: {e}")
                os.remove(cv_path)
                os.remove(jd_path)
                st.stop()
        else:
            jd_text = jd_text_paste
        # Split CV into sections (robust)
        from core.cv_handler import extract_sections
        sections_dict = extract_sections(cv_text)
        section_titles_list = list(sections_dict.keys())
        section_texts = list(sections_dict.values())
        from core.scorer import section_relevance
        # Get all section scores
        import numpy as np
        try:
            from sentence_transformers import SentenceTransformer, util
            model = SentenceTransformer('all-MiniLM-L6-v2')
            jd_emb = model.encode(jd_text, convert_to_tensor=True)
            cv_embs = model.encode(section_texts, convert_to_tensor=True)
            scores = util.pytorch_cos_sim(cv_embs, jd_emb).cpu().numpy().flatten()
        except Exception as e:
            st.error(f"Error computing section relevance: {e}")
            os.remove(cv_path)
            if jd_path: os.remove(jd_path)
            st.stop()
        import pandas as pd
        df = pd.DataFrame({
            "Section Title": section_titles_list,
            "Score": np.round(scores, 2)
        })
        df = df.sort_values("Score", ascending=False)
        # Show sorted bar chart (descending order)
        st.bar_chart(df.set_index("Section Title"))
        if len(sections_dict) < 3:
            st.warning("Your CV was split into fewer than 3 sections. Consider adjusting your section headers in the sidebar for better relevance analysis.")
        # Recommend section headers based on scores
        def recommend_section_headers(sections_dict, scores, threshold=0.5):
            """
            Recommend section headers to include based on relevance scores.
            Returns a list of section names with scores above the threshold (default 0.5).
            """
            return [section for section, score in zip(sections_dict.keys(), scores) if score >= threshold]
        recommended_headers = recommend_section_headers(sections_dict, scores)
        if recommended_headers:
            st.info(f"Recommended section headers to include: {', '.join(recommended_headers)}")
        else:
            st.info("No section headers strongly recommended based on relevance scores. Consider revising your CV or section headers.")
        # Clean up temp files
        os.remove(cv_path)
        if jd_path: os.remove(jd_path)

# After LLM output, score the AI-generated sections
        st.subheader("Section Relevance Preview (Tailored CV)")
        if 'tailored_cv' in locals() and tailored_cv:
            ai_sections_dict = extract_sections(tailored_cv)
            ai_section_titles = list(ai_sections_dict.keys())
            ai_section_texts = list(ai_sections_dict.values())
            try:
                ai_cv_embs = model.encode(ai_section_texts, convert_to_tensor=True)
                ai_scores = util.pytorch_cos_sim(ai_cv_embs, jd_emb).cpu().numpy().flatten()
            except Exception as e:
                st.error(f"Error computing tailored CV section relevance: {e}")
                st.stop()
            ai_df = pd.DataFrame({
                "Section Title": ai_section_titles,
                "Score": np.round(ai_scores, 2)
            })
            ai_df = ai_df.sort_values("Score", ascending=False)
            st.bar_chart(ai_df.set_index("Section Title"))

    # --- INTERVIEW PROBABILITY UI ---
    if cv_file and (jd_file or jd_text_paste.strip()):
        try:
            prob_before = compute_interview_probability(cv_text, jd_text)
            st.session_state['prob_before'] = prob_before
            st.sidebar.subheader("Interview Probability Estimate (Before Tailoring)")
            st.sidebar.metric("Estimated Probability to Get Interview", f"{int(prob_before*100)}%", delta=None, delta_color="inverse")
        except Exception as e:
            st.sidebar.error(f"Could not compute interview probability: {e}")
