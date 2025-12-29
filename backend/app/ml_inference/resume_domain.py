from backend.app.ml_inference.model_loader import load_model

_domain_model = load_model("domain_model.pkl")
_domain_vectorizer = load_model("domain_vectorizer.pkl")

def predict_domain(text: str) -> str:
    if not text or not text.strip():
        return "Unknown"

    text = text.lower().strip()
    vector = _domain_vectorizer.transform([text])
    return _domain_model.predict(vector)[0]
