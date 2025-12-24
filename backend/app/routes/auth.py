from flask import Blueprint, request, jsonify, render_template, redirect, url_for,Response
import pickle
import pandas as pd
import numpy as np
import os
import re
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords

auth = Blueprint('auth', __name__, template_folder='templates', url_prefix='/auth')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON provided"}), 400

        username = data.get('username')
        password = data.get('password')

        # Example authentication logic
        if username == 'admin' and password == 'password':
            return jsonify({"message": "Login successful",
                            'username': username,
                            'role': 'admin ',
                            'password':password}), 200
        else:
            return jsonify({"error": "Invalid credentials"}), 401



BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "../../ml/models")

with open(os.path.join(MODEL_DIR, "g1_model.pkl"), "rb") as f:
    g1_model = pickle.load(f)

with open(os.path.join(MODEL_DIR, "g2_model.pkl"), "rb") as f:
    g2_model = pickle.load(f)

with open(os.path.join(MODEL_DIR, "g3_model.pkl"), "rb") as f:
    g3_model = pickle.load(f)

print("Progressive student performance models loaded successfully!")


with open(os.path.join(MODEL_DIR, "final_svm_model.pkl"), "rb") as f:
    fake_review_model = pickle.load(f)

with open(os.path.join(MODEL_DIR, "tfidf_vectorizer.pkl"), "rb") as f:
    fake_review_tfidf = pickle.load(f)

print("Fake review detection models loaded successfully!")

with open(os.path.join(MODEL_DIR, "course_recommender_tfidf.pkl"), "rb") as f:
    course_tfidf = pickle.load(f)

with open(os.path.join(MODEL_DIR, "course_similarity_matrix.pkl"), "rb") as f:
    course_sim_matrix = pickle.load(f)

df_courses = pd.read_pickle(
    os.path.join(MODEL_DIR, "course_recommender_dataset.pkl")
)

print("Course recommendation models loaded successfully!")


def get_course_recommendations(course_name, top_n=5):
    course_name = course_name.lower()

    # Match user input with dataset
    matches = df_courses[df_courses["clean_name"].str.contains(course_name, case=False, na=False)]

    if len(matches) == 0:
        return None  # no match found

    idx = matches.index[0]

    # Get similarity scores
    sim_scores = list(enumerate(course_sim_matrix[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)

    # Top-N (skip itself)
    sim_scores = sim_scores[1 : top_n + 1]

    recommended_indices = [i[0] for i in sim_scores]

    return df_courses.iloc[recommended_indices][
        ["Course Name", "University", "Difficulty Level", "Course Rating", "Skills"]
    ]


# ============================
# PREPROCESS REVIEW TEXT
# ============================

nltk.download('stopwords', quiet=True)
nltk.download('punkt', quiet=True)
nltk.download('wordnet', quiet=True)

stop_words = set(stopwords.words("english"))
lemmatizer = WordNetLemmatizer()

def clean_review(text):
    """Clean input review for fake review detection."""
    text = text.lower()
    text = re.sub(r"[^a-z\s]", " ", text)
    tokens = text.split()
    tokens = [lemmatizer.lemmatize(w) for w in tokens if w not in stop_words]
    return " ".join(tokens)

# ============================
# ROUTES
# ============================

@auth.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "API is running successfully!",
        "route": {
            "/predict-pass": "POST — Predict pass/fail",
            "/predict-cgpa": "POST — Predict CGPA level",
            "/predict-fake-review": "POST — Detect fake employee review"
        }
    })

# ----------------------------
# Student Performance — PASS/FAIL
# ----------------------------
def stage_detect(data):
    if "G1" not in data:
        return 1
    if "G2" not in data:
        return 2
    return 3

@auth.route("/predict-cgpa", methods=["POST"])
def predict_cgpa():
    data = request.json
    df = pd.DataFrame([data])

    stage = stage_detect(data)

    if stage == 1:
        g1 = g1_model.predict(df)[0]
        cgpa = (g1 / 20.0) * 10.0
        cgpa = max(0.0, min(cgpa, 10.0))

        return jsonify({
            "predicted_cgpa": round(float(cgpa), 2),
            "derived_from": "Predicted G1",
            "stage": "Stage 1 (Early)"
        })

    if stage == 2:
        g2 = g2_model.predict(df)[0]
        cgpa = (g2 / 20.0) * 10.0
        cgpa = max(0.0, min(cgpa, 10.0))

        return jsonify({
            "predicted_cgpa": round(float(cgpa), 2),
            "derived_from": "Predicted G2",
            "stage": "Stage 2 (Mid)"
        })

    cgpa = g3_model.predict(df)[0]
    cgpa = max(0.0, min(cgpa, 10.0))

    return jsonify({
        "predicted_cgpa": round(float(cgpa), 2),
        "derived_from": "Predicted G3",
        "stage": "Stage 3 (Final)"
    })


@auth.route("/predict-pass", methods=["POST"])
def predict_pass():
    data = request.json
    df = pd.DataFrame([data])

    if stage_detect(data) != 3:
        return jsonify({
            "error": "Pass/Fail prediction requires G1 and G2"
        }), 400

    cgpa = g3_model.predict(df)[0]
    cgpa = max(0.0, min(cgpa, 10.0))

    return jsonify({
        "predicted_cgpa": round(float(cgpa), 2),
        "prediction": int(cgpa >= 5.0)
    })


# ----------------------------
# Fake Review Detection
# ----------------------------
@auth.route("/predict-fake-review", methods=["POST"])
def predict_fake_review():
    data = request.json
    review_text = data.get("review", "")

    if not review_text:
        return jsonify({"error": "Missing 'review' field"}), 400

    cleaned = clean_review(review_text)
    print("Cleaned Review:", cleaned)

    vector = fake_review_tfidf.transform([cleaned])
    pred = fake_review_model.predict(vector)[0]

    # LinearSVC probability
    try:
        prob = fake_review_model._predict_proba_lr(vector)[0][1]
    except:
        prob = float(abs(fake_review_model.decision_function(vector)[0]))

    return jsonify({
        "is_fake": int(pred),
        "label": "deceptive" if pred == 1 else "truthful",
        "confidence": float(prob)
    })

# ----------------------------
# COURSE RECOMMENDATION SYSTEM (MODULE 2)
# ----------------------------
@auth.route("/recommend-courses", methods=["POST"])
def recommend_courses_api():
    data = request.json

    course_name = data.get("course_name", "")
    top_n = data.get("top_n", 5)

    if not course_name:
        return jsonify({"error": "Missing 'course_name' field"}), 400

    recommendations = get_course_recommendations(course_name, top_n)

    if recommendations is None:
        return jsonify({"error": "Course not found"}), 404

    return jsonify({
        "input_course": course_name,
        "recommendations": recommendations.to_dict(orient="records")
    })