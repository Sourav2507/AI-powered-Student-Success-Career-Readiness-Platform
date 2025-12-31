from flask import Blueprint, json, request, jsonify, render_template, redirect, url_for,send_file,session
from dotenv import load_dotenv
from openai import OpenAI
import os
import requests
import markdown
import tempfile
import os
import tempfile
import redis
import hashlib
from backend.app.utils.resume_parser import extract_text
from backend.app.utils.skill_extractor import extract_skills
from backend.app.utils.experience_parser import extract_experience
from backend.app.utils.academic_parser import extract_academics
from backend.app.scoring.ats_scorer import calculate_ats_score
from backend.app.llm.resume_summary import generate_resume_summary
from backend.app.llm.skill_level_inferencer import infer_skill_levels
from backend.app.ml_inference.resume_domain import predict_domain
from backend.app.ml_inference.resume_job_role import predict_job_roles
from backend.app.async_celery.tasks import fetch_and_cache_jobs, job_cache_key


from pptx import Presentation
from pptx.util import Pt, Inches


load_dotenv()

user = Blueprint('user', __name__, template_folder='templates', url_prefix='/user')

@user.route('/profile', methods=['GET'])
def profile():
    return render_template('profile.html')

@user.route('/chatbot', methods=['GET'])
def chatbot():
    return render_template('chatbot.html',
    active_menu="learning-tools",
    active_submenu="chatbot")

@user.route('/ppt_gen', methods=['GET'])
def ppt_gen():
    return render_template('ppt_gen.html',
    active_menu="learning-tools",
    active_submenu="ppt")

@user.route('/exam', methods=['GET'])
def exam():
    return render_template('exam.html', mode="form",
    active_menu="learning-tools",
    active_submenu="exam")

@user.route('/dashboard', methods=['GET'])
def dashboard():
    return render_template('user_db.html',
    active_menu="dashboard")

@user.route('/stress_assessment', methods=['GET'])
def stress_assessment():
    return render_template('stress.html',
    active_menu="dashboard")

@user.route('/resume_analyzer', methods=['GET'])
def resume_analyzer():
    return render_template('resume.html',
    active_menu="learning-tools",
    active_submenu="resume")

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


@user.route('/base')
def base():
    return render_template('base.html', active_menu ='learning-tools',active_submenu='resume')








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
        total=len(questions),
    active_menu="learning-tools",
    active_submenu="exam"
    )

@user.route("/api/resume/analyze", methods=["POST"])
def analyze_resume():
    if "file" not in request.files:
        return jsonify({"error": "Resume file is required"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    _, ext = os.path.splitext(file.filename)

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        file.save(tmp.name)
        temp_path = tmp.name

    try:
        # -------- 1. Resume parsing --------
        resume_text = extract_text(temp_path)

        skills = extract_skills(resume_text)
        experience = extract_experience(resume_text)
        academics = extract_academics(resume_text)

        domain = predict_domain(resume_text)
        job_roles = predict_job_roles(resume_text)

        ats_result = calculate_ats_score(
            skills=skills,
            experience=experience,
            academics=academics,
            domain=domain
        )

        response = {
            "domain": domain,
            "job_roles": job_roles,
            "skills": skills,
            "experience": experience,
            "academics": academics,
            "ats_score": ats_result["ats_score"],
            "score_breakdown": ats_result["breakdown"]
        }

        # -------- 2. LLM enrichment (SAFE) --------
        try:
            llm_context = {
                "domain": domain,
                "job_roles": job_roles,
                "skills": skills,
                "experience": experience,
                "academics": academics,
                "ats_score": ats_result["ats_score"]
            }
            response["summary"] = generate_resume_summary(llm_context)
            response["skill_levels"] = infer_skill_levels(resume_text, skills)
        except Exception:
            response["summary"] = None
            response["skill_levels"] = {}

        # -------- 3. Background job fetching --------
        cache_key = job_cache_key(job_roles, "india")

        # Prevent duplicate Celery jobs
        status = redis_client.get(cache_key + ":status")
        if not status:
            redis_client.setex(
                cache_key + ":status",
                JOB_CACHE_TTL,
                "pending"
            )
            fetch_and_cache_jobs.delay(job_roles, "india")

        response["jobs_cache_key"] = cache_key

        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

redis_client = redis.Redis(
    host="localhost",
    port=6379,
    db=2,
    decode_responses=True
)

JOB_CACHE_TTL = 60 * 15  # 15 minutes


def job_cache_key(roles, location="india"):
    raw = f"{','.join(sorted(roles))}:{location}"
    return "jobs:" + hashlib.md5(raw.encode()).hexdigest()


@user.route("/api/jobs/status", methods=["GET"])
def jobs_status():
    cache_key = request.args.get("cache_key")
    if not cache_key:
        return jsonify({"error": "cache_key required"}), 400

    status = redis_client.get(cache_key + ":status")

    return jsonify({
        "status": status if status else "not_started"
    })

@user.route("/api/jobs/results", methods=["GET"])
def jobs_results():
    cache_key = request.args.get("cache_key")
    if not cache_key:
        return jsonify({"error": "cache_key required"}), 400

    cached = redis_client.get(cache_key)
    if not cached:
        return jsonify({
            "ready": False,
            "jobs": []
        })

    # Refresh TTL on read (optional but good UX)
    redis_client.expire(cache_key, JOB_CACHE_TTL)
    redis_client.expire(cache_key + ":status", JOB_CACHE_TTL)

    return jsonify({
        "ready": True,
        "jobs": json.loads(cached)
    })
