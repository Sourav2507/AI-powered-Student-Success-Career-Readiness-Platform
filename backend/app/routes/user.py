from flask import Blueprint, json, request, jsonify, render_template, redirect, url_for,send_file,session
from dotenv import load_dotenv
from openai import OpenAI
import os
import requests
import markdown
import tempfile
from pptx import Presentation
from pptx.util import Pt, Inches


load_dotenv()

user = Blueprint('user', __name__, template_folder='templates', url_prefix='/user')

@user.route('/profile', methods=['GET'])
def profile():
    return render_template('profile.html')

@user.route('/chatbot', methods=['GET'])
def chatbot():
    return render_template('chatbot.html')

@user.route('/ppt_gen', methods=['GET'])
def ppt_gen():
    return render_template('ppt_gen.html')

@user.route('/exam', methods=['GET'])
def exam():
    return render_template('exam.html', mode="form")

@user.route("/questions")
def questions():
    if "questions" not in session:
        return redirect("/user/exam")

    # Convert list into [(index, question), ...]
    questions = list(enumerate(session["questions"]))

    return render_template(
        "questions.html",
        questions=questions
    )











@user.route("/chat", methods=["POST"])
def chat():
    history = request.json.get("history", [])
    msg = request.json.get("message")

    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")

    def format_history(history):
        formatted = []
        for h in history:
            role = "user" if h["sender"] == "user" else "assistant"
            formatted.append({"role": role, "content": h["content"]})
        return formatted

    formatted_messages = format_history(history) + [
        {"role": "user", "content": msg}
    ]

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {openrouter_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost",
                "X-Title": "My Flask App",
            },
            json={
                "model": "openai/gpt-oss-120b:free",
                "messages": formatted_messages
            },
            timeout=12
        )

        data = response.json()

        if "error" in data:
            raise Exception(f"OpenRouter error: {data['error']}")

        raw_text = data["choices"][0]["message"]["content"]
        data["choices"][0]["message"]["content"] = markdown.markdown(
            raw_text,
            extensions=["tables", "fenced_code", "nl2br", "sane_lists"]
        )

        return jsonify(data)

    except Exception as e:
        print("OpenRouter failed → Switching to GROQ:", e)

    groq_models = [
        "llama-3.3-70b-versatile",
        "gemma2-9b-it",
        "llama-3.1-8b-instant"
    ]

    for model in groq_models:
        try:
            print(f"Trying GROQ model: {model}")

            groq_response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {groq_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": formatted_messages
                },
                timeout=12
            )

            data = groq_response.json()
            print("GROQ RESPONSE:", data)

            if "error" in data or "choices" not in data:
                print(f"Model {model} failed → trying next model...\n")
                continue

            raw_text = data["choices"][0]["message"]["content"]
            data["choices"][0]["message"]["content"] = markdown.markdown(
                raw_text,
                extensions=["tables", "fenced_code", "nl2br", "sane_lists"]
            )

            return jsonify(data)

        except Exception as e:
            print(f"GROQ model {model} crashed → {e}")

    return jsonify({
        "error": "All models failed (OpenRouter + Groq models)",
        "details": "Rate limits or network issues"
    }), 500

@user.route('/generate_questions', methods=['POST'])
def generate_questions():
    topic = request.form.get("topic")
    difficulty = request.form.get("difficulty")

    prompt = f"""
    Generate 10 multiple-choice questions for the topic '{topic}' at '{difficulty}' difficulty.
    Return STRICT JSON ONLY in this format:

    [
    {{
        "question": "....",
        "options": {{
            "A": "Option text 1",
            "B": "Option text 2",
            "C": "Option text 3",
            "D": "Option text 4"
        }},
        "correct": "A"
    }}
    ]
    ]
    """


    # Call your LLM using the same /chat endpoint
    response = requests.post(
        url_for('user.chat', _external=True),
        json={"message": prompt, "history": []}
    ).json()

    raw_json = response["choices"][0]["message"]["content"]

    # If markdown messed it up, remove HTML tags
    import re
    raw_json = re.sub(r"<[^>]+>", "", raw_json).strip()


    # Some models return code block ```json ... ```
    if "```" in raw_json:
        raw_json = raw_json.split("```")[1]
        raw_json = raw_json.replace("json", "").strip()

    questions = json.loads(raw_json)

    # Store questions in session
    session["questions"] = questions

    return redirect(url_for('user.questions'))

@user.route('/submit_exam', methods=['POST'])
def submit_exam():
    questions = session.get("questions", [])
    results = []
    score = 0

    for i, q in enumerate(questions):

        # Extract ONLY the letter (A/B/C/D)
        user_ans = request.form.get(f"q{i}")
        if user_ans:
            user_ans = user_ans.strip()[0]   # Take the first character ONLY

        correct = q["correct"]

        results.append({
            "question": q["question"],
            "options": q["options"],
            "selected": user_ans,
            "correct": correct,
            "is_correct": user_ans == correct
        })

        if user_ans == correct:
            score += 1

    return render_template(
        "exam.html",
        mode="result",
        results=results,
        score=score,
        total=len(questions)
    )
