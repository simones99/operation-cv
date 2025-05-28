# 🧠 Operation CV

### Tailor your CV with AI—privately and locally.
Operation CV is a privacy-first, local AI-powered tool that helps you rewrite and optimize your CV for any job description—entirely on your machine. Built with Python, Streamlit, and local LLMs via LM Studio, this app parses your CV and job descriptions, scores relevance, tailors your content, and estimates your interview probability—all without sending a single byte to the cloud.
---

## 🚀 Features
  ### 📄 CV & Job Description Parsing
    Upload your CV and job description in PDF, DOCX, or TXT formats. The app robustly extracts sections from real-world, messy CVs and JDs.
  ### 📊 Section Relevance Scoring
    Each CV section is semantically compared to the job description. Get a visual bar chart showing what matches—and what doesn’t.
  ###	🧬 AI Tailoring with Local LLMs
    Run your favorite Mistral, LLaMA 3, or other models locally via LM Studio to rewrite your CV for the job and industry you choose.
  ### 🧠 Interview Probability Estimation
    See a before-and-after estimate of how likely your CV is to land an interview, based on keyword and semantic overlap.
  ### 🏭 Industry-Aware Prompting
  Custom prompts guide the LLM based on the selected industry—tech, finance, healthcare, and more.
  ### 🖼️ Streamlit UI
  A smooth, responsive UI with file upload, live previews, downloadable results, and error handling—all in a single-page web app.


---

## ⚡ Quick Start

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

### 🧪 How It Works
- Upload Your CV & Job Description
- The app parses both files and breaks them into logical sections
- Each CV section is scored for relevance using semantic similarity
- Local LLM rewrites your CV based on job/industry context
- App displays:
	-	Tailored CV preview
	-	Section relevance bar chart
	-	Interview probability score: original vs. optimized
-	Download your optimized CV as DOCX or PDF

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
- Built with ❤️ and a strong belief in user data privacy