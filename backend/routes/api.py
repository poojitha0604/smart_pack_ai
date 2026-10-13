from flask import Blueprint, jsonify, request

from models import database as db
from services import dl_service, ml_service, pipeline
from utils.validation import ALIASES, parse_recommend_payload

api = Blueprint("api", __name__)


def guess_from_filename(filename):
    """Demo-mode guess: the longest food name found in the file name wins
    (so potato_chips.jpg -> Potato Chips, not Potato)."""
    import re
    text = " " + re.sub(r"[^a-z]+", " ", filename.lower()) + " "
    keys = {n.lower(): n for n in db.list_foods()}
    keys.update({a.lower(): v for a, v in ALIASES.items()})
    hits = [k for k in keys if " " + k + " " in text or k.replace(" ", "") in text.replace(" ", "")]
    return keys[max(hits, key=len)] if hits else None


@api.get("/health")
def health():
    return jsonify({"status": "ok", "dl_model_loaded": dl_service.available(),
                    "ml_model_loaded": ml_service.available(), "database": "mysql" if db.IS_MYSQL else "sqlite"})


@api.get("/foods")
def foods():
    return jsonify(db.list_foods())


@api.post("/detect-food")
def detect_food():
    f = request.files.get("image")
    if not f:
        return jsonify({"error": "Upload an image in the 'image' field"}), 400
    result = dl_service.detect(f.read())
    if result:
        return jsonify(result)
    # No trained DL model yet -> demo mode: guess from the file name, user confirms.
    guess = guess_from_filename(f.filename or "")
    return jsonify({
        "status": "model_unavailable",
        "predictions": [{"food": guess, "probability": None}] if guess else [],
        "message": "Trained DL model not found (run dl/train_model.py). Please confirm the food manually.",
    })


@api.post("/recommend")
def recommend():
    clean, err = parse_recommend_payload(request.get_json(silent=True) or {})
    if err:
        return jsonify({"error": err}), 400
    try:
        return jsonify(pipeline.process_recommendation(
            clean["food"], clean["shelf_life"], clean["storage"], clean["transport"], clean["temperature"],
            clean["travel_hours"]))
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


@api.get("/food/<name>")
def food(name):
    f = db.get_food(name)
    return (jsonify(f), 200) if f else (jsonify({"error": "Food not found"}), 404)


@api.get("/packaging/<pid>")
def packaging(pid):
    p = db.get_packaging(pid)
    return (jsonify(p), 200) if p else (jsonify({"error": "Packaging not found"}), 404)


@api.get("/history")
def history():
    return jsonify(db.history())
