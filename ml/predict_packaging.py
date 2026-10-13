"""
Predict packaging from the trained model.

CLI:  python ml/predict_packaging.py --food Tomato --shelf-life 12 --storage Chilled --transport Long --temp 5
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

MODEL_PATH = ROOT / "ml" / "models" / "packaging_model.joblib"
_pipe = None


def model_available():
    return MODEL_PATH.exists()


def _load():
    global _pipe
    if _pipe is None:
        import joblib
        _pipe = joblib.load(MODEL_PATH)
    return _pipe


def make_row(food, moisture, fat, ph, respiration, shelf_life, storage, transport, temperature):
    return {
        "food_name": food, "moisture_level": moisture, "fat_level": fat, "ph_category": ph,
        "respiration_level": respiration, "required_shelf_life": shelf_life, "storage_type": storage,
        "storage_temperature": temperature, "transportation_type": transport,
    }


def predict_row(row, top_k=3):
    import pandas as pd
    pipe = _load()
    proba = pipe.predict_proba(pd.DataFrame([row]))[0]
    classes = list(pipe.named_steps["model"].classes_)
    order = sorted(range(len(classes)), key=lambda i: proba[i], reverse=True)[:top_k]
    top = [{"packaging_name": classes[i], "probability": float(proba[i])} for i in order]
    return {"packaging_name": top[0]["packaging_name"], "probability": top[0]["probability"], "top": top}


def predict(food, shelf_life, storage, transport, temperature):
    """Convenience wrapper that looks the food up in the reference data."""
    from database.reference_data import FOODS
    f = FOODS[food]
    row = make_row(food, f["moisture"], f["fat"], f["ph"], f["respiration"], shelf_life, storage, transport, temperature)
    return predict_row(row)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--food", required=True)
    ap.add_argument("--shelf-life", type=int, required=True)
    ap.add_argument("--storage", default="Chilled", choices=["Ambient", "Chilled", "Frozen"])
    ap.add_argument("--transport", default="Medium", choices=["Short", "Medium", "Long"])
    ap.add_argument("--temp", type=float, default=5)
    a = ap.parse_args()
    if not model_available():
        sys.exit("Model not found. Run: python ml/generate_dataset.py  then  python ml/train_model.py")
    res = predict(a.food.title(), a.shelf_life, a.storage, a.transport, a.temp)
    print(f"Recommended packaging: {res['packaging_name']}")
    print(f"Model probability: {res['probability']:.2f}")
    for t in res["top"][1:]:
        print(f"  also considered: {t['packaging_name']} ({t['probability']:.2f})")
