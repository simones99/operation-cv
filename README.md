# 🥷🏻 Operation CV

### Tailor your CV with AI—privately and locally.

Operation CV is a privacy-first, local AI-powered tool that helps you rewrite and optimize your CV for any job description—entirely on your machine. Built with Python, Streamlit, and local LLMs via LM Studio, this app parses your CV and job descriptions, scores relevance, tailors your content, and estimates your interview probability—all without sending a single byte to the cloud.

---

## 🚀 Features

### 📄 CV & Job Description Parsing
- Upload your CV and job descriptions in PDF, DOCX, or TXT formats
- Robust section extraction from real-world, messy CVs and JDs
- Smart section normalization for consistent template mapping
- Automatic skill extraction and matching

### 📊 Advanced Scoring System
- **Interview Probability Score**: Get a clear percentage of how well your CV matches the job
- **Target Score Setting**: Set your desired interview probability and get tailored suggestions
- **Component Analysis**:
  - Content Match (50%): Semantic alignment with job requirements
  - Skill Coverage (30%): Required skills found in your CV
  - Keyword Density (20%): Effective use of relevant keywords
- **Gap Analysis**: See exactly how far you are from your target score

### 🎯 Smart Suggestions
- Personalized improvement recommendations based on your scores
- Missing skills identification and integration suggestions
- Content alignment tips for better semantic matching
- Keyword optimization guidance

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
- Interactive probability scoring dashboard
- Visual component score analysis
- Progress tracking for long operations
- Detailed error messages and recovery

---

## ⚡ Quick Start

1. **Install Python 3.10 or 3.11**
   ```sh
   # Using pyenv (recommended)
   pyenv install 3.11
   pyenv local 3.11
   # Or use your OS package manager
   ```

2. **Clone the Repository**
   ```sh
   git clone https://github.com/yourusername/OperationCV.git
   cd OperationCV
   ```

3. **Set Up Virtual Environment**
   ```sh
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

4. **Install Requirements**
   ```sh
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

5. **Install & Run LM Studio**
   - Download [LM Studio](https://lmstudio.ai/)
   - Run a local LLM (Mistral, Llama 3, etc.) on port 1234
   - Model must support OpenAI-compatible chat API

6. **Run the App**
   ```sh
   streamlit run app/streamlit_app.py
   ```

---

## 📊 Understanding the Scoring System

### Interview Probability Score
The overall score is calculated using three weighted components:
- **Content Match (50%)**: Semantic similarity between your CV and the job description
- **Skill Coverage (30%)**: Percentage of required skills found in your CV
- **Keyword Density (20%)**: How effectively you've used relevant keywords

### Target Score
1. Set your desired interview probability (default 80%)
2. The system will:
   - Calculate the gap between current and target scores
   - Provide specific suggestions to reach your target
   - Highlight areas needing immediate improvement

### Component Scores
Each component is scored from 0-100%:
- **Content Match**: Uses semantic analysis to measure how well your content aligns
- **Skill Coverage**: Compares required skills with those in your CV
- **Keyword Density**: Analyzes the effective use of relevant keywords

---

## 🎯 Using Templates

1. Check `/template/example_template.md` for available variables
2. Use the default template in `/template/cv_template.docx`
3. Or create your own DOCX template using the variables
4. Upload your template in the app's sidebar
5. Your template will be used for all exports (DOCX and PDF)

---

## 🛠️ Advanced Configuration

### JSON Schema
The CV structure is defined in `core/cv_schema.json` and includes:
- Required sections (summary, experience, education, skills)
- Optional sections (projects, publications, languages)
- Validation rules for each section
- Format requirements and constraints

### Language Models
- Default port: 1234 (configurable)
- Supported models: Any OpenAI-compatible chat model
- Recommended: Mistral-7B, LLaMA-3, or similar
- Min 8GB VRAM recommended

---

## 🎯 Best Practices

1. **CV Preparation**
   - Use clear section headings
   - Include quantifiable achievements
   - Keep formatting simple
   - Use standard section names

2. **Job Description Analysis**
   - Include full job posting
   - Ensure requirements section is included
   - More detail = better matching

3. **Template Usage**
   - Test templates with sample data first
   - Keep styling minimal
   - Use all required variables
   - Follow spacing guidelines

4. **Optimal Results**
   - Set realistic target scores
   - Review and implement all suggestions
   - Focus on gap analysis recommendations
   - Update skills section comprehensively

---

## 🔄 Recent Updates

- Fixed JSON schema and parsing for CV suggestions
- Improved error handling and logging in LLM client
- Enhanced suggestion display in the UI
- Updated CV schema to better match LLM response format
- Added better validation for JSON responses
- Fixed percentage calculation issues
- Added comprehensive scoring documentation

### LLM Response Format

The system expects LLM responses in this JSON format:
```json
{
  "sections": {
    "summary": "Improved summary content...",
    "education": "Improved education content...",
    "experience": "Improved experience content...",
    "skills": "Improved skills content..."
  }
}
```

Each section contains the improved content as a string, which can include:
- Line breaks (`\n`) for formatting
- Bullet points for better readability
- Original content structure preserved
- Enhanced wording and phrasing
- Better keyword placement

---

## 🚀 Roadmap

- [ ] Advanced template gallery
- [ ] Custom industry instruction editor
- [ ] Batch processing of multiple CVs
- [ ] Enhanced skill extraction
- [ ] More language support
- [ ] Docker deployment
- [ ] Template sharing system
- [ ] Enhanced PDF formatting
- [ ] AI-powered template recommendations
- [ ] Historical score tracking
- [ ] Comparative analysis features

---

## 📝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- LLM support via [LM Studio](https://lmstudio.ai/)
- Semantic analysis using [Sentence Transformers](https://www.sbert.net/)
