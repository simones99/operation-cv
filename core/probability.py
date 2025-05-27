from sentence_transformers import SentenceTransformer, util

MODEL_NAME = 'all-MiniLM-L6-v2'

def compute_interview_probability(cv_text, jd_text, model=None):
    """
    Compute a probability (0-1) of getting an interview based on affinity between skills/profile and job offer.
    Uses semantic similarity between the full CV and JD, and boosts for strong skill matches.
    """
    if model is None:
        model = SentenceTransformer(MODEL_NAME)
    # Compute overall similarity
    emb = model.encode([cv_text, jd_text], convert_to_tensor=True)
    sim = float(util.pytorch_cos_sim(emb[0], emb[1]).item())
    # Normalize to 0-1
    base_prob = (sim + 1) / 2
    # Extract skills from CV and JD (simple keyword match, can be improved)
    import re
    def extract_skills(text):
        # Look for lines or comma-separated lists after 'Skills', 'Competenze', etc.
        skills = set()
        for line in text.splitlines():
            if re.search(r'skills|competenze|abilities|compértences', line, re.IGNORECASE):
                # Split by comma or semicolon
                skills.update([s.strip().lower() for s in re.split(r'[,:;•]', line) if len(s.strip()) > 1])
        return skills
    cv_skills = extract_skills(cv_text)
    jd_skills = extract_skills(jd_text)
    # Compute skill overlap
    if cv_skills and jd_skills:
        overlap = len(cv_skills & jd_skills) / max(1, len(jd_skills))
    else:
        overlap = 0
    # Weighted probability: 70% semantic, 30% skill overlap
    prob = 0.7 * base_prob + 0.3 * overlap
    return round(prob, 2)
