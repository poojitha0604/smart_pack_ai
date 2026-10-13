"""Food detection. Uses the trained MobileNetV2 model if present, otherwise returns None."""
import logging

log = logging.getLogger(__name__)


def available():
    try:
        from dl.predict_food import model_available
        return model_available()
    except Exception:  # noqa: BLE001
        return False


def detect(image_bytes):
    if not available():
        return None
    try:
        from dl.predict_food import predict_bytes
        return predict_bytes(image_bytes)
    except Exception as e:  # noqa: BLE001  (TensorFlow missing, corrupt image, ...)
        log.warning("DL prediction failed: %s", e)
        return None
