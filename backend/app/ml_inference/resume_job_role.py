import numpy as np
from backend.app.ml_inference.model_loader import load_model

_job_model = load_model("job_role_model.pkl")
_job_vectorizer = load_model("job_role_vectorizer.pkl")

def predict_job_roles(text: str, top_n: int = 3):
    if not text or not text.strip():
        return []

    text = text.lower().strip()
    vector = _job_vectorizer.transform([text])
    scores = _job_model.decision_function(vector)

    if scores.ndim == 1:
        return [_job_model.classes_[0]]

    indices = np.argsort(scores[0])[::-1][:top_n]
    return [_job_model.classes_[i] for i in indices]