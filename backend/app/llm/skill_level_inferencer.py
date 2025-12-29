# backend/app/llm/skill_level_inferencer.py

import json
import re
from backend.app.llm.llm_router import call_llm
from backend.app.llm.prompts import SKILL_LEVEL_PROMPT


def infer_skill_levels(resume_text: str, skills: list) -> dict:
    if not skills:
        return {}

    prompt = SKILL_LEVEL_PROMPT.format(
        skills=", ".join(skills),
        resume_text=resume_text[:3000]
    )

    messages = [
        {"role": "user", "content": prompt}
    ]

    raw = call_llm(messages)

    # Cleanup markdown / HTML
    raw = re.sub(r"<[^>]+>", "", raw).strip()
    if "```" in raw:
        raw = raw.split("```")[1].replace("json", "").strip()

    try:
        return json.loads(raw)
    except Exception:
        return {}
