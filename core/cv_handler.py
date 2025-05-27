import pdfplumber
import docx
import os
import re
from typing import Dict

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

def extract_cv_text(path):
    """Detect file type and extract text from CV."""
    ext = os.path.splitext(path)[1].lower()
    if ext == '.pdf':
        return extract_text_from_pdf(path)
    elif ext == '.docx':
        return extract_text_from_docx(path)
    elif ext == '.txt':
        return extract_text_from_txt(path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

def extract_sections(cv_text: str) -> Dict[str, str]:
    """
    Hybrid: Extracts sections by scanning for known headers (any case) and any ALL CAPS line with 2+ words.
    This is robust for CVs with custom or standard all-caps section headers.
    """
    section_headers = [
        'professional summary', 'summary', 'profile', 'objective',
        'experience', 'work experience', 'professional experience', 'additional experience',
        'education', 'academic background',
        'skills', 'technical skills', 'core competencies', 'skills & certifications', 'skills and certifications',
        'certifications', 'projects', 'publications', 'languages', 'interests', 'awards', 'activities',
        'volunteer', 'volunteering', 'extracurricular', 'extra curricular', 'additional / extra curricular experience',
        'contact', 'personal information', 'references'
    ]
    def normalize(header):
        h = header.lower().replace('&', 'and').replace('/', ' ').replace('-', ' ')
        h = re.sub(r'[^a-z0-9 ]+', '', h)
        h = re.sub(r'\s+', ' ', h).strip()
        return h
    normalized_headers = {normalize(h): h for h in section_headers}
    lines = cv_text.splitlines()
    section_indices = []
    for idx, line in enumerate(lines):
        norm = normalize(line)
        # Known header match (any case)
        if norm in normalized_headers:
            section_indices.append((idx, normalized_headers[norm].title()))
            continue
        # ALL CAPS, 2+ words, mostly letters/numbers/symbols
        line_stripped = line.strip()
        if (
            len(line_stripped.split()) >= 2 and
            line_stripped.upper() == line_stripped and
            re.match(r'^[A-Z0-9 &/().,\'-]+$', line_stripped)
        ):
            section_indices.append((idx, line_stripped.title()))
    if not section_indices:
        return {'Full CV': cv_text.strip()}
    sections = {}
    for i, (start_idx, section_name) in enumerate(section_indices):
        end_idx = section_indices[i+1][0] if i+1 < len(section_indices) else len(lines)
        content = '\n'.join(lines[start_idx+1:end_idx]).strip()
        if content:
            sections[section_name] = content
    return sections

def parse_cv_file(file_path: str) -> Dict[str, str]:
    """
    Parses a CV file and returns a dict of section_name: section_content.
    """
    cv_text = extract_cv_text(file_path)
    return extract_sections(cv_text)