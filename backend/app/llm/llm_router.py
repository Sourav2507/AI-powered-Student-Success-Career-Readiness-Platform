# backend/app/llm/llm_router.py

import os
import requests

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

OPENROUTER_MODEL = "openai/gpt-oss-120b:free"
GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "gemma2-9b-it",
    "llama-3.1-8b-instant"
]


def call_llm(messages, timeout=12):
    """
    Try OpenRouter first, fallback to Groq models.
    Returns raw text output.
    """

    # -------------------------
    # OpenRouter
    # -------------------------
    openrouter_key = os.getenv("OPENROUTER_API_KEY")

    if openrouter_key:
        try:
            response = requests.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {openrouter_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://localhost",
                    "X-Title": "Mentora Resume Analyzer",
                },
                json={
                    "model": OPENROUTER_MODEL,
                    "messages": messages
                },
                timeout=timeout
            )

            data = response.json()

            if "choices" in data:
                return data["choices"][0]["message"]["content"]

        except Exception as e:
            print("OpenRouter failed →", e)

    # -------------------------
    # Groq fallback
    # -------------------------
    groq_key = os.getenv("GROQ_API_KEY")

    for model in GROQ_MODELS:
        try:
            response = requests.post(
                GROQ_URL,
                headers={
                    "Authorization": f"Bearer {groq_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages
                },
                timeout=timeout
            )

            data = response.json()

            if "choices" in data:
                return data["choices"][0]["message"]["content"]

        except Exception as e:
            print(f"GROQ {model} failed →", e)

    raise RuntimeError("All LLM providers failed")
