# backend/app/llm/resume_summary.py

from backend.app.llm.llm_router import call_llm
from backend.app.llm.prompts import SUMMARY_PROMPT


def generate_resume_summary(context: dict) -> str:
    prompt = SUMMARY_PROMPT.format(context=context)

    messages = [
        {"role": "user", "content": prompt}
    ]

    return call_llm(messages).strip()
