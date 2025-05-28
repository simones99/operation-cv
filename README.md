# 🧠 Operation CV

### Tailor your CV with AI—privately and locally.

Operation CV is a privacy-first, local AI-powered tool that helps you rewrite and optimize your CV for any job description—entirely on your machine. Built with Python, Streamlit, and local LLMs via LM Studio, this app parses your CV and job descriptions, scores relevance, tailors your content, and estimates your interview probability—all without sending a single byte to the cloud.

---

## 🚀 Features

### 📄 CV & Job Description Parsing
- Upload your CV and job descriptions in PDF, DOCX, or TXT formats
- Robust section extraction from real-world, messy CVs and JDs
- Smart section normalization for consistent template mapping

### 📊 Section Relevance Analysis
- Semantic comparison of each CV section against job requirements
- Visual bar chart showing section-by-section relevance
- Color-coded scoring with detailed explanations

### 🎨 Template System
- Customizable DOCX templates for consistent CV formatting
- Default template included with professional layout
- Variables for all common CV sections:
  - `{{ summary }}` - Professional summary/profile
  - `{{ experience }}` - Work experience
  - `{{ education }}` - Education
  - `{{ skills }}` - Skills & competencies
  - And more! See `/template/example_template.md`

### 🧬 AI Tailoring with Local LLMs
- Run your favorite Mistral, LLaMA 3, or other models locally via LM Studio
- Industry-specific prompting for targeted optimization
- Language selection (English UK/US, French, Spanish, Italian)

### 📊 Interview Probability Estimation
- Before-and-after probability scoring
- Based on keyword matching and semantic similarity
- Industry-specific scoring adjustments

### 💾 Save & Export
- Save applications to SQLite database for future reference
- Export as DOCX or PDF using your templates
- View and re-export previous applications

### 🏭 Industry-Aware Features
- Custom prompts per industry
- Industry-specific scoring adjustments
- Tailored suggestions based on sector

### 🖼️ Enhanced UI/UX
- Clean, responsive Streamlit interface
- Progress tracking for long operations
- Detailed error messages and recovery
- File cleanup and management
- Template preview and validation

---

## ⚡ Quick Start

1. **Install Python 3.10 or 3.11**
   - Use [pyenv](https://github.com/pyenv/pyenv) or your OS package manager

2. **Set Up Virtual Environment**
   ```sh
   python3.11 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Requirements**
   ```sh
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Install & Run LM Studio**
   - Download [LM Studio](https://lmstudio.ai/)
   - Run a local LLM (Mistral, Llama 3, etc.) on port 1234
   - Model must support OpenAI-compatible chat API

5. **Run the App**
   ```sh
   streamlit run app/streamlit_app.py
   ```

---

## 🎯 Using Templates

1. Check `/template/example_template.md` for available variables
2. Use the default template in `/template/cv_template.docx`
3. Or create your own DOCX template using the variables
4. Upload your template in the app's sidebar
5. Your template will be used for all exports (DOCX and PDF)

---

## 🧪 How It Works

1. **File Upload & Processing**
   - Upload CV & Job Description
   - Smart parsing into logical sections
   - Template validation and preparation

2. **Analysis**
   - Section-by-section semantic scoring
   - Keyword extraction and matching
   - Interview probability calculation

3. **AI Optimization**
   - Industry-specific prompt generation
   - Local LLM tailoring of content
   - Section normalization for template

4. **Output & Storage**
   - Preview tailored content
   - Apply template formatting
   - Save to database (optional)
   - Export as DOCX or PDF

---

## 🛠️ Troubleshooting

### Common Issues
- **Template errors:**
  - Ensure DOCX templates use correct variable syntax
  - Check `/template/example_template.md` for valid variables
  - Use the default template as a reference

- **Dependency errors:**
  - Use Python 3.10 or 3.11 (3.13 may have ML library issues)
  - Check `requirements.txt` for correct versions
  - For `tokenizers`, `sentencepiece`, or `huggingface_hub` errors, reinstall requirements

- **LM Studio connection:**
  - Ensure LM Studio is running on port 1234
  - Check for OpenAI-compatible API at `http://127.0.0.1:1234/v1/chat/completions`

- **File issues:**
  - Try different file formats if parsing fails
  - Check for file corruption
  - Ensure proper section headings in CVs

### Error Recovery
- The app includes automatic cleanup of temporary files
- Failed operations won't leave orphaned files
- You can always regenerate outputs

---

## 📁 Project Structure

```text
OperationCV/
├── app/
│   └── streamlit_app.py      # Main Streamlit application
├── core/
│   ├── cv_handler.py         # CV parsing and processing
│   ├── file_utils.py         # File management utilities
│   ├── industry_instructions # Industry-specific prompts
│   ├── jd_handler.py         # Job description processing
│   ├── llm_client.py        # Local LLM interaction
│   ├── probability.py        # Interview probability calc
│   ├── prompt_utils.py       # Prompt management
│   └── save_utils.py         # File saving utilities
├── template/
│   ├── cv_template.docx      # Default CV template
│   ├── example_template.md   # Template documentation
│   └── README.md            # Template usage guide
├── prompts/                  # System prompts
├── outputs/                  # Generated files
└── requirements.txt         # Python dependencies
```

---

## 🚀 Recent Improvements

- Added template system with variable documentation
- Enhanced file management and cleanup
- Improved error handling and user feedback
- Added better saved applications viewer
- Template validation and verification
- Progress tracking for long operations
- Automatic template fallback
- Enhanced PDF export quality

---

## 🏗️ Future Development

- [ ] Advanced template gallery
- [ ] Custom industry instruction editor
- [ ] Batch processing of multiple CVs
- [ ] Enhanced skill extraction
- [ ] More language support
- [ ] Docker deployment
- [ ] Template sharing system
- [ ] Enhanced PDF formatting

---

## 📝 License

See `LICENSE` file for details.

---

## 🤝 Contributing

Contributions are welcome! Please check the issues page for current tasks.
