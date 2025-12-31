from flask import Blueprint, request, jsonify
import pickle, os, joblib
import pandas as pd
import numpy as np

ml = Blueprint('ml', __name__, template_folder='templates', url_prefix='/ml')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "../../ml/models")





with open(os.path.join(MODEL_DIR, "g1_model.pkl"), "rb") as f:
    g1_model = pickle.load(f)

with open(os.path.join(MODEL_DIR, "g2_model.pkl"), "rb") as f:
    g2_model = pickle.load(f)

with open(os.path.join(MODEL_DIR, "g3_model.pkl"), "rb") as f:
    g3_model = pickle.load(f)

def stage_detect(data):
    if "G1" not in data:
        return 1
    if "G2" not in data:
        return 2
    return 3

@ml.route("/predict-cgpa", methods=["POST"])
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


@ml.route("/predict-pass", methods=["POST"])
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




fake_review_pipeline = joblib.load(
    os.path.join(MODEL_DIR, "fake_review_hybrid_model.pkl")
)

@ml.route("/predict-fake-review", methods=["POST"])
def predict_fake_review():
    data = request.json

    review_text = data.get("review", "")
    rating = data.get("rating", None)
    category = data.get("category", "")

    if not review_text or rating is None or not category:
        return jsonify({
            "error": "Required fields: review, rating, category"
        }), 400

    input_df = pd.DataFrame([{
        "clean_text": review_text,
        "rating": rating,
        "category": category
    }])

    proba = fake_review_pipeline.predict_proba(input_df)[0]
    confidence = float(max(proba))
    pred = int(proba[1] >= 0.5)

    threshold = 0.70

    if confidence < threshold:
        return jsonify({
            "is_fake": 1,
            "is_truthful": 0,
            "label": "deceptive",
            "confidence": confidence,
            "note": "Low probability → treated as fake"
        })

    return jsonify({
        "is_fake": int(pred == 0),
        "is_truthful": int(pred == 1),
        "label": "deceptive" if pred == 0 else "truthful",
        "confidence": confidence
    })




with open(os.path.join(MODEL_DIR, "course_recommender_tfidf.pkl"), "rb") as f:
    course_tfidf = pickle.load(f)

with open(os.path.join(MODEL_DIR, "course_similarity_matrix.pkl"), "rb") as f:
    course_sim_matrix = pickle.load(f)

df_courses = pd.read_pickle(
    os.path.join(MODEL_DIR, "course_recommender_dataset.pkl")
)

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

@ml.route("/recommend-courses", methods=["POST"])
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



rf_model = joblib.load(
    os.path.join(MODEL_DIR, "stress_level_random_forest.pkl")
)

scaler = joblib.load(
    os.path.join(MODEL_DIR, "stress_level_scaler.pkl")
)

# Stress level mapping
stress_map = {
    0: "Low",
    1: "Medium",
    2: "High"
}

@ml.route("/api/predict-stress", methods=["POST"])
def predict_stress():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No input data provided"}), 400

        # Expected 20 features in correct order
        features = [
            data["anxiety_level"],
            data["self_esteem"],
            data["mental_health_history"],
            data["depression"],
            data["headache"],
            data["blood_pressure"],
            data["sleep_quality"],
            data["breathing_problem"],
            data["noise_level"],
            data["living_conditions"],
            data["basic_needs"],
            data["academic_performance"],
            data["study_load"],
            data["teacher_student_relationship"],
            data["future_career_concerns"],
            data["social_support"],
            data["peer_pressure"],
            data["extracurricular_activities"],
            data["bullying"],
            data["confidence_level"]  # replace if different column
        ]

        # Convert to array
        X = np.array(features).reshape(1, -1)

        # Scale
        X_scaled = scaler.transform(X)

        # Predict
        prediction = rf_model.predict(X_scaled)[0]
        probabilities = rf_model.predict_proba(X_scaled)[0]

        return jsonify({
            "stress_level_numeric": int(prediction),
            "stress_level": stress_map[prediction],
            "confidence_scores": {
                "Low": round(float(probabilities[0]), 3),
                "Medium": round(float(probabilities[1]), 3),
                "High": round(float(probabilities[2]), 3)
            }
        })

    except KeyError as e:
        return jsonify({"error": f"Missing field: {str(e)}"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500