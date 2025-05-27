from typing import Dict
from sentence_transformers import SentenceTransformer, util
import numpy as np

MODEL_NAME = 'all-MiniLM-L6-v2'
model = SentenceTransformer(MODEL_NAME)

def match_score(cv_text, jd_text):
    """Compute cosine similarity between the full CV and JD text."""
    emb = model.encode([cv_text, jd_text], convert_to_tensor=True)
    return util.pytorch_cos_sim(emb[0], emb[1]).item()

def section_relevance(cv_sections: Dict[str, str], jd_text: str, model_name: str = 'all-MiniLM-L6-v2') -> Dict[str, float]:
    """
    Scores each CV section for relevance to the job description using semantic similarity.
    Returns a dict of section_name: relevance_score (0-1).
    """
    model = SentenceTransformer(model_name)
    jd_emb = model.encode(jd_text, convert_to_tensor=True)
    scores = {}
    for section, content in cv_sections.items():
        if not content.strip():
            scores[section] = 0.0
            continue
        section_emb = model.encode(content, convert_to_tensor=True)
        sim = float(util.pytorch_cos_sim(section_emb, jd_emb).item())
        # Normalize to 0-1 (cosine sim is -1 to 1)
        norm_score = (sim + 1) / 2
        scores[section] = round(norm_score, 3)
    return scores

# --- INTERVIEW PROBABILITY SCORING ---
# (Moved to core/probability.py)
