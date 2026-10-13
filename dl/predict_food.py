r"""
Predict the food in an image.

CLI:  python dl/predict_food.py path\to\tomato.jpg
      Prints e.g.   Predicted class: Tomato   /   Probability: 0.94

      python dl/predict_food.py --folder path\to\my_photos
      Test the model on YOUR OWN photos. Put them in sub-folders named like the classes
      (my_photos\tomato\a.jpg, my_photos\potato_chips\b.jpg ...). Prints accuracy and every mistake.

Note: softmax "probability" is not calibrated confidence. Validate before calling it confidence.
"""
import io
import json
import sys
from pathlib import Path

MODEL_DIR = Path(__file__).resolve().parent / "models"
_cache = {}


def model_available():
    return (MODEL_DIR / "food_model.keras").exists() and (MODEL_DIR / "class_names.json").exists()


def _load():
    if not _cache:
        from tensorflow import keras  # imported lazily so the backend starts without TensorFlow
        _cache["model"] = keras.models.load_model(MODEL_DIR / "food_model.keras")
        _cache["classes"] = json.loads((MODEL_DIR / "class_names.json").read_text(encoding="utf-8"))
        cfg = MODEL_DIR / "config.json"
        _cache["threshold"] = json.loads(cfg.read_text())["threshold"] if cfg.exists() else 0.60
    return _cache


def predict_pil(img, top_k=3):
    import numpy as np
    c = _load()
    arr = np.asarray(img.convert("RGB").resize((224, 224)), dtype="float32")[None, ...]
    proba = c["model"].predict(arr, verbose=0)[0]
    order = np.argsort(proba)[::-1][:top_k]
    preds = [{"food": c["classes"][i], "probability": float(proba[i])} for i in order]
    status = "ok" if preds[0]["probability"] >= c["threshold"] else "low_confidence"
    return {"status": status, "predictions": preds, "threshold": c["threshold"]}


def predict_image(path, top_k=3):
    from PIL import Image
    return predict_pil(Image.open(path), top_k)


def predict_bytes(data, top_k=3):
    from PIL import Image
    return predict_pil(Image.open(io.BytesIO(data)), top_k)


def pretty(folder_name):
    return folder_name.replace("_", " ").title()


def test_folder(folder):
    exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    total = right = unsure = 0
    wrong = []
    for sub in sorted(p for p in Path(folder).iterdir() if p.is_dir()):
        truth = pretty(sub.name)
        for img in sorted(sub.iterdir()):
            if img.suffix.lower() not in exts:
                continue
            r = predict_image(img)
            top = r["predictions"][0]
            total += 1
            unsure += r["status"] == "low_confidence"
            if top["food"] == truth:
                right += 1
            else:
                wrong.append(f"  {img.name}: is {truth}, predicted {top['food']} ({top['probability']:.2f})")
    if not total:
        sys.exit("No images found. Use sub-folders named after the classes, e.g. my_photos/tomato/a.jpg")
    print(f"Accuracy on your photos: {right}/{total} = {right / total:.1%}  (low-probability, would ask to confirm: {unsure})")
    print("\n".join(wrong) if wrong else "No mistakes.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Usage: python dl/predict_food.py <image_path>   or   --folder <folder_of_class_subfolders>")
    if not model_available():
        sys.exit("No trained model found. Run: python dl/train_model.py")
    if sys.argv[1] == "--folder":
        test_folder(sys.argv[2])
        sys.exit(0)
    r = predict_image(sys.argv[1])
    print(f"Predicted class: {r['predictions'][0]['food']}")
    print(f"Probability: {r['predictions'][0]['probability']:.2f}")
    if r["status"] == "low_confidence":
        print("Low probability - ask the user to confirm. Other matches:",
              ", ".join(p["food"] for p in r["predictions"][1:]))
