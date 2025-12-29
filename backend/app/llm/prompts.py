# backend/app/llm/prompts.py

SUMMARY_PROMPT = """
You are an expert resume analyst.

Write a concise 3–4 line professional summary.
Do not exaggerate or invent experience.

Candidate Data:
{context}
"""

SKILL_LEVEL_PROMPT = """
You are a technical recruiter.

Classify each skill as Beginner, Intermediate, or Advanced.
Use ONLY resume evidence.
If unsure, choose Beginner.

Return STRICT JSON ONLY.

Skills:
{skills}

Resume Text:
{resume_text}
"""
