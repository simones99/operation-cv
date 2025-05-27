# CV Tailor Agent

A privacy-first, local AI tool to tailor your CV to any job description. Built with Python, Streamlit, and local LLMs (via LM Studio), this app helps you generate a job-specific CV and estimate your interview probability—all on your machine, with no data leaving your device.

---

## Features
- **Robust CV & JD Parsing:** Supports PDF, DOCX, and TXT for both CV and job description. Handles real-world CV sectioning.
- **Automatic Section Relevance:** Semantic similarity scoring for each CV section vs. the job description, with bar chart visualization.
- **Local LLM Tailoring:** Uses LM Studio (Mistral or other local models) to rewrite your CV for the target job and industry.
- **Industry-Aware Prompting:** Custom instructions for different industries/sectors.
- **Interview Probability Estimate:** Calculates your chance of getting an interview before and after tailoring, based on semantic and skill overlap.
- **User-Friendly UI:** Streamlit interface with error handling, file upload, and download of tailored CV (DOCX/PDF).

---

## Quick Start

### 1. **Install Python 3.10 or 3.11**
- Use [pyenv](https://github.com/pyenv/pyenv) or your OS package manager.

### 2. **Set Up Virtual Environment**
```sh
python3.11 -m venv .venv
source .venv/bin/activate
```

### 3. **Install Requirements**
```sh
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. **Install & Run LM Studio**
- Download [LM Studio](https://lmstudio.ai/) and run a local LLM (e.g., Mistral, Llama 3, etc.) on port 1234.
- Make sure the model supports chat/completion API compatible with OpenAI format.

### 5. **Run the App**
```sh
streamlit run app/streamlit_app.py
```

---

## Usage
1. **Upload your CV** (PDF, DOCX, or TXT).
2. **Upload or paste the Job Description**.
3. **Select output language, format, and industry** in the sidebar.
4. **Click "Tailor My CV"**. Wait for the local LLM to generate your tailored CV.
5. **Preview and download** the tailored CV. See section relevance and interview probability before/after tailoring in the sidebar.

---

## Troubleshooting
- **Dependency errors:**
  - Use Python 3.10 or 3.11. Newer versions (e.g., 3.13) may not work with ML libraries.
  - If you see errors about `tokenizers`, `sentencepiece`, or `huggingface_hub`, ensure you have the correct versions (see `requirements.txt`).
- **LM Studio not running:**
  - Make sure LM Studio is open and a model is running on port 1234.
  - The app expects an OpenAI-compatible chat API at `http://127.0.0.1:1234/v1/chat/completions`.
- **File parsing errors:**
  - Ensure your files are not empty or corrupted. Try saving as a different format if issues persist.
- **Section relevance/embedding errors:**
  - Make sure all dependencies are installed and your Python version is supported.

---

## Next Steps & Development
- **Skill Extraction:** Improve skill extraction for more accurate interview probability.
- **Advanced Error Handling:** Add more robust logging and user feedback.
- **Batch Processing:** Allow tailoring multiple CVs/JDs at once.
- **Editable Prompts/Instructions:** Let users edit industry instructions inline.
- **Unit Tests:** Add tests for core modules and parsing logic.
- **Dockerization:** Add a Dockerfile for easy deployment.
- **UI Polish:** Add more visual feedback, progress bars, and customization options.

---

## Project Structure
```
core/
    cv_handler.py         # CV parsing and section extraction
    jd_handler.py         # Job description parsing
    scorer.py             # Section relevance scoring
    probability.py        # Interview probability calculation
    llm_client.py         # LLM API client
    save_utils.py         # Export utilities
    prompt_utils.py       # Prompt loading
    industry_instructions.py # Industry-specific instructions
app/
    streamlit_app.py      # Main Streamlit UI
prompts/
    cv_tailor_system.txt  # System prompt for LLM
outputs/                  # Generated tailored CVs
```

---

## Credits
- Built by Simone Mezzabotta, 2025
- MIT License