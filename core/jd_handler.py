import pdfplumber
import docx
import os

def extract_text_from_pdf(path):
    """Extract text from a PDF file using pdfplumber."""
    with pdfplumber.open(path) as pdf:
        return "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())

def extract_text_from_docx(path):
    """Extract text from a DOCX file using python-docx."""
    doc = docx.Document(path)
    return "\n".join([para.text for para in doc.paragraphs if para.text.strip()])

def extract_text_from_txt(path):
    """Extract text from a TXT file."""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def extract_jd_text(path):
    """Detect file type and extract text from Job Description."""
    ext = os.path.splitext(path)[1].lower()
    if ext == '.pdf':
        return extract_text_from_pdf(path)
    elif ext == '.docx':
        return extract_text_from_docx(path)
    elif ext == '.txt':
        return extract_text_from_txt(path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")
