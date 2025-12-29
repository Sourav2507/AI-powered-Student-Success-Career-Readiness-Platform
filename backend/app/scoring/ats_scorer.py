# backend/app/scoring/ats_scorer.py

# -------------------------------------------------
# ATS WEIGHT CONFIGURATION
# -------------------------------------------------

SKILL_WEIGHT = 40
EXPERIENCE_WEIGHT = 25
ACADEMIC_WEIGHT = 20
DOMAIN_WEIGHT = 15


# -------------------------------------------------
# SKILL SCORING
# -------------------------------------------------

def _score_skills(skills: list) -> int:
    """
    Score based on number of CS skills found.
    """
    if not skills:
        return 0

    # Cap skill contribution
    max_skills = 10
    score = min(len(skills), max_skills) / max_skills

    return int(score * SKILL_WEIGHT)


# -------------------------------------------------
# EXPERIENCE SCORING
# -------------------------------------------------

def _score_experience(experience: dict) -> int:
    level = experience.get("experience_level", "Unknown")

    mapping = {
        "Fresher": 0.4,
        "Junior": 0.6,
        "Mid-level": 0.8,
        "Senior": 1.0
    }

    return int(mapping.get(level, 0) * EXPERIENCE_WEIGHT)


# -------------------------------------------------
# ACADEMIC SCORING
# -------------------------------------------------

def _score_academics(academics: dict) -> int:
    degree = academics.get("degree")

    mapping = {
        "B.Tech": 0.7,
        "B.E": 0.7,
        "B.Sc": 0.6,
        "M.Tech": 0.9,
        "M.E": 0.9,
        "M.Sc": 0.8,
        "MCA": 0.85,
        "PhD": 1.0
    }

    return int(mapping.get(degree, 0.5) * ACADEMIC_WEIGHT)


# -------------------------------------------------
# DOMAIN SCORING
# -------------------------------------------------

def _score_domain(domain: str) -> int:
    if not domain:
        return 0
    return DOMAIN_WEIGHT


# -------------------------------------------------
# FINAL ATS SCORE FUNCTION
# -------------------------------------------------

def calculate_ats_score(
    skills: list,
    experience: dict,
    academics: dict,
    domain: str
):
    """
    Calculate ATS score (0-100) with breakdown.
    """

    skill_score = _score_skills(skills)
    experience_score = _score_experience(experience)
    academic_score = _score_academics(academics)
    domain_score = _score_domain(domain)

    total_score = (
        skill_score +
        experience_score +
        academic_score +
        domain_score
    )

    return {
        "ats_score": min(total_score, 100),
        "breakdown": {
            "skills": skill_score,
            "experience": experience_score,
            "academics": academic_score,
            "domain": domain_score
        }
    }
