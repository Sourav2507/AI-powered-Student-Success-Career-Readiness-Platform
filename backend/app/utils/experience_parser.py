import re


# -------------------------------------------------
# EXPERIENCE PARSING LOGIC
# -------------------------------------------------

YEAR_PATTERN = re.compile(
    r"(\d+(\.\d+)?)\s*(\+)?\s*(years|year|yrs|yr)",
    re.IGNORECASE
)

DATE_RANGE_PATTERN = re.compile(
    r"(20\d{2})\s*[-–]\s*(20\d{2}|present)",
    re.IGNORECASE
)


def extract_experience(resume_text: str):
    """
    Extract total years of experience from resume text.

    Args:
        resume_text (str)

    Returns:
        dict:
            {
              "total_experience": float,
              "experience_level": str
            }
    """

    if not resume_text or not resume_text.strip():
        return {
            "total_experience": 0.0,
            "experience_level": "Unknown"
        }

    text = resume_text.lower()

    years_found = []

    # -------------------------
    # 1. Explicit year mentions
    # -------------------------
    for match in YEAR_PATTERN.findall(text):
        try:
            years = float(match[0])
            years_found.append(years)
        except ValueError:
            pass

    # -------------------------
    # 2. Date range estimation
    # Example: 2019 - 2023
    # -------------------------
    for match in DATE_RANGE_PATTERN.findall(text):
        start_year = int(match[0])
        end = match[1]

        if end.lower() == "present":
            end_year = 2025  # current year (safe assumption)
        else:
            end_year = int(end)

        duration = max(0, end_year - start_year)
        if duration > 0:
            years_found.append(duration)

    # -------------------------
    # 3. Final estimation
    # -------------------------
    total_experience = max(years_found) if years_found else 0.0

    experience_level = _classify_experience(total_experience)

    return {
        "total_experience": round(total_experience, 1),
        "experience_level": experience_level
    }


def _classify_experience(years: float) -> str:
    """
    Classify experience into levels.
    """

    if years == 0:
        return "Fresher"
    elif years < 2:
        return "Junior"
    elif years < 5:
        return "Mid-level"
    else:
        return "Senior"
