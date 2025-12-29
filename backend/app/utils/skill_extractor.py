import re

# -------------------------------------------------
# MASTER CS SKILL LIST (CURATED & EXPLAINABLE)
# -------------------------------------------------

CS_SKILLS = {
    # Programming Languages
    "Python", "Java", "C", "C++", "JavaScript", "TypeScript", "Go", "Rust",

    # Data Science & ML
    "Machine Learning", "Deep Learning", "Data Science", "Statistics",
    "Pandas", "NumPy", "Scikit Learn", "TensorFlow", "PyTorch",
    "NLP", "Computer Vision",

    # Web Development
    "HTML", "CSS", "React", "Angular", "Vue", "Node", "Express",
    "Django", "Flask", "REST API",

    # Databases
    "SQL", "MySQL", "PostgreSQL", "MongoDB", "Redis",

    # Cloud & DevOps
    "AWS", "Azure", "GCP", "Docker", "Kubernetes",
    "CI CD", "Jenkins", "GitHub Actions", "Terraform",

    # Software Engineering
    "Data Structures", "Algorithms", "OOP", "System Design",
    "Design Patterns", "Microservices",

    # Tools
    "Git", "GitHub", "Linux", "Shell Scripting"
}


# -------------------------------------------------
# NORMALIZATION UTILITIES
# -------------------------------------------------

def _normalize_text(text: str) -> str:
    """
    Normalize text for reliable matching.
    """
    text = text.lower()
    text = re.sub(r"[^a-z0-9+ ]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _normalize_skill(skill: str) -> str:
    """
    Normalize skill names to match normalized resume text.
    """
    return skill.lower().replace(".", "").strip()


# -------------------------------------------------
# MAIN SKILL EXTRACTION FUNCTION
# -------------------------------------------------

def extract_skills(resume_text: str):
    """
    Extract CS-related skills from resume text.

    Args:
        resume_text (str): Raw resume text

    Returns:
        list: Sorted list of unique skills found
    """

    if not resume_text or not resume_text.strip():
        return []

    normalized_text = _normalize_text(resume_text)

    found_skills = set()

    for skill in CS_SKILLS:
        skill_norm = _normalize_skill(skill)

        # Word-boundary aware matching
        pattern = r"\b" + re.escape(skill_norm) + r"\b"

        if re.search(pattern, normalized_text):
            found_skills.add(skill)

    return sorted(found_skills)
