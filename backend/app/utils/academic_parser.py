import re


# -------------------------------------------------
# DEGREE & FIELD TAXONOMY (CS-FOCUSED)
# -------------------------------------------------

DEGREE_PATTERNS = {
    "B.Tech": r"(b\.?tech|bachelor of technology)",
    "B.E": r"(b\.?e\.?|bachelor of engineering)",
    "B.Sc": r"(b\.?sc|bachelor of science)",
    "M.Tech": r"(m\.?tech|master of technology)",
    "M.E": r"(m\.?e\.?|master of engineering)",
    "M.Sc": r"(m\.?sc|master of science)",
    "MCA": r"(mca|master of computer applications)",
    "PhD": r"(ph\.?d|doctorate)"
}

FIELD_PATTERNS = {
    "Computer Science": r"(computer science|cse)",
    "Information Technology": r"(information technology|it)",
    "Artificial Intelligence": r"(artificial intelligence|ai)",
    "Data Science": r"(data science)",
    "Machine Learning": r"(machine learning)",
    "Software Engineering": r"(software engineering)"
}


# -------------------------------------------------
# MAIN ACADEMIC PARSER
# -------------------------------------------------

def extract_academics(resume_text: str):
    """
    Extract academic background from resume text.

    Returns:
        dict:
        {
          "degree": str | None,
          "field": str | None,
          "education_level": str
        }
    """

    if not resume_text or not resume_text.strip():
        return {
            "degree": None,
            "field": None,
            "education_level": "Unknown"
        }

    text = resume_text.lower()

    degree_found = None
    field_found = None

    # -------------------------
    # Degree detection
    # -------------------------
    for degree, pattern in DEGREE_PATTERNS.items():
        if re.search(pattern, text):
            degree_found = degree
            break

    # -------------------------
    # Field detection
    # -------------------------
    for field, pattern in FIELD_PATTERNS.items():
        if re.search(pattern, text):
            field_found = field
            break

    education_level = _classify_education_level(degree_found)

    return {
        "degree": degree_found,
        "field": field_found,
        "education_level": education_level
    }


def _classify_education_level(degree: str | None) -> str:
    if not degree:
        return "Unknown"
    if degree.startswith("B"):
        return "Undergraduate"
    if degree.startswith("M"):
        return "Postgraduate"
    if degree == "PhD":
        return "Doctorate"
    return "Unknown"