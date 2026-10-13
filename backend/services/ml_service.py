"""Packaging prediction. Uses the trained joblib pipeline if present, otherwise returns None."""
import logging

log = logging.getLogger(__name__)


def available():
    try:
        from ml.predict_packaging import model_available
        return model_available()
    except Exception:  # noqa: BLE001
        return False


def predict(food, shelf_life, storage, transport, temperature):
    """food: dict from the database (moisture, fat, ph, respiration, name)."""
    if not available():
        return None
    try:
        from ml.predict_packaging import make_row, predict_row
        row = make_row(food["name"], food["moisture"], food["fat"], food["ph"], food["respiration"],
                       shelf_life, storage, transport, temperature)
        return predict_row(row)
    except Exception as e:  # noqa: BLE001
        log.warning("ML prediction failed, using rules: %s", e)
        return None
