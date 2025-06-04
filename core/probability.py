from sentence_transformers import SentenceTransformer, util
import re
from typing import Dict, List, Tuple

MODEL_NAME = 'all-MiniLM-L6-v2'

def extract_skills_and_requirements(text: str) -> List[str]:
    """Extract skills and requirements from text."""
    skills = set()
    for line in text.splitlines():
        if re.search(r'skills|competenze|abilities|compétences|requirements|qualifications', line, re.IGNORECASE):
            # Split by common delimiters
            parts = re.split(r'[,:;•\n]', line)
            # Clean and add each skill
            for part in parts:
                clean = part.strip().lower()
                if len(clean) > 2 and not re.match(r'^(and|or|the|skills|required|preferred)$', clean):
                    skills.add(clean)
    return list(skills)

def get_semantic_similarity(cv_text: str, jd_text: str, model=None) -> float:
    """Compute semantic similarity between CV and job description."""
    if model is None:
        model = SentenceTransformer(MODEL_NAME)
    emb = model.encode([cv_text, jd_text], convert_to_tensor=True)
    sim = float(util.pytorch_cos_sim(emb[0], emb[1]).item())
    return (sim + 1) / 2  # Normalize to 0-1

def analyze_missing_skills(cv_text: str, jd_text: str) -> Tuple[List[str], List[str], List[str]]:
    """Analyze which skills are missing or could be emphasized."""
    cv_skills = set(extract_skills_and_requirements(cv_text))
    jd_skills = set(extract_skills_and_requirements(jd_text))
    
    missing = list(jd_skills - cv_skills)
    matching = list(cv_skills & jd_skills)
    extra = list(cv_skills - jd_skills)
    
    return missing, matching, extra

def compute_interview_probability(cv_text: str, jd_text: str, model=None) -> Dict:
    """
    Compute probability of getting an interview based on CV and job description match.
    Returns a dict with probability score and component scores.
    """
    if model is None:
        model = SentenceTransformer(MODEL_NAME)

    # Compute base semantic similarity (50% weight)
    semantic_score = get_semantic_similarity(cv_text, jd_text, model)
    
    # Analyze skills overlap (30% weight)
    missing, matching, extra = analyze_missing_skills(cv_text, jd_text)
    jd_skills = extract_skills_and_requirements(jd_text)
    skill_coverage = len(matching) / max(1, len(jd_skills)) if jd_skills else 0.0
    
    # Calculate keyword density score (20% weight)
    keywords = set(jd_skills)
    if keywords:
        cv_words = set(w.lower() for w in cv_text.split())
        keyword_matches = len(cv_words.intersection(keywords))
        keyword_density = min(1.0, keyword_matches / len(keywords))
    else:
        keyword_density = 0.0
    
    # Calculate final weighted probability
    prob = (0.5 * semantic_score) + (0.3 * skill_coverage) + (0.2 * keyword_density)
    
    return {
        'probability': max(0.01, min(1.0, round(prob, 2))),  # Ensure between 1-100%
        'semantic_score': round(semantic_score, 2),
        'skill_coverage': round(skill_coverage, 2),
        'keyword_density': round(keyword_density, 2),
        'missing_skills': missing,
        'matching_skills': matching,
        'extra_skills': extra
    }
