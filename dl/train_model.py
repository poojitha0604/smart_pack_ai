"""
Train the food image classifier (MobileNetV2 transfer learning) on datasets/images/<class>/.

Steps: read images -> 70/15/15 stratified split -> augmentation -> train the new head ->
fine-tune the top MobileNetV2 layers -> evaluate on the untouched test set -> choose the
confirmation threshold from the VALIDATION set -> save everything to dl/models/.

Usage:  python dl/train_model.py [--head-epochs 10] [--finetune-epochs 8] [--threshold 0.6]
Prepare the data first:  python datasets/prepare_dataset.py --help
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from threshold import choose_threshold  # noqa: E402

DATA = ROOT / "datasets" / "images"
OUT = ROOT / "dl" / "models"
IMG, BATCH, EXT = (224, 224), 32, {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def pretty(folder_name):
    """potato_chips -> Potato Chips (must match the food names in database/reference_data.py)"""
    return folder_name.replace("_", " ").title()


def collect(class_names):
    paths, labels, skipped = [], [], 0
    for idx, cls in enumerate(class_names):
        for p in sorted((DATA / cls).iterdir()):
            if p.suffix.lower() not in EXT:
                continue
            try:
                with Image.open(p) as im:
                    im.verify()
            except Exception:  # noqa: BLE001
                skipped += 1
                continue
            paths.append(str(p)); labels.append(idx)
    if skipped:
        print(f"Skipped {skipped} unreadable images")
    return paths, labels


def make_ds(paths, labels, training):
    ds = tf.data.Dataset.from_tensor_slices((paths, labels))
    def load(path, label):
        img = tf.io.decode_image(tf.io.read_file(path), channels=3, expand_animations=False)
        return tf.image.resize(img, IMG), label
    ds = ds.map(load, num_parallel_calls=tf.data.AUTOTUNE)
    if training:
        ds = ds.shuffle(1000, seed=42)
    return ds.batch(BATCH).prefetch(tf.data.AUTOTUNE)


def predict_all(model, ds):
    probs, y = [], []
    for xb, yb in ds:
        probs.append(model.predict(xb, verbose=0)); y += yb.numpy().tolist()
    return np.concatenate(probs), np.array(y)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--head-epochs", type=int, default=10)
    ap.add_argument("--finetune-epochs", type=int, default=8, help="0 to skip fine-tuning")
    ap.add_argument("--threshold", type=float, default=None, help="fixed threshold; default: chosen from validation data")
    a = ap.parse_args()

    class_names = sorted(d.name for d in DATA.iterdir() if d.is_dir())
    paths, labels = collect(class_names)
    counts = {pretty(c): labels.count(i) for i, c in enumerate(class_names)}
    print("Images per class:", counts)
    thin = [c for c, n in counts.items() if n < 20]
    if thin:
        sys.exit(f"Too few images (<20) for: {thin}. Run datasets/prepare_dataset.py or add photos to datasets/images/<class>/.")

    p_tr, p_tmp, y_tr, y_tmp = train_test_split(paths, labels, test_size=0.30, stratify=labels, random_state=42)
    p_va, p_te, y_va, y_te = train_test_split(p_tmp, y_tmp, test_size=0.50, stratify=y_tmp, random_state=42)
    train_ds, val_ds, test_ds = make_ds(p_tr, y_tr, True), make_ds(p_va, y_va, False), make_ds(p_te, y_te, False)
    print(f"train {len(p_tr)} / validation {len(p_va)} / test {len(p_te)}")

    augment = keras.Sequential([layers.RandomFlip("horizontal"), layers.RandomRotation(0.12),
                                layers.RandomZoom(0.2), layers.RandomContrast(0.2), layers.RandomBrightness(0.2)])
    base = keras.applications.MobileNetV2(input_shape=IMG + (3,), include_top=False, weights="imagenet")
    base.trainable = False
    inputs = keras.Input(shape=IMG + (3,))
    x = augment(inputs)                                   # active only during training
    x = layers.Rescaling(1 / 127.5, offset=-1)(x)         # MobileNetV2 expects [-1, 1]
    x = base(x, training=False)                           # keeps BatchNorm in inference mode
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dropout(0.3)(x)
    outputs = layers.Dense(len(class_names), activation="softmax")(x)
    model = keras.Model(inputs, outputs)

    stop = lambda: keras.callbacks.EarlyStopping(patience=3, restore_best_weights=True)   # noqa: E731
    model.compile(optimizer=keras.optimizers.Adam(1e-3), loss="sparse_categorical_crossentropy", metrics=["accuracy"])
    hist = model.fit(train_ds, validation_data=val_ds, epochs=a.head_epochs, callbacks=[stop()])
    history = {k: list(v) for k, v in hist.history.items()}

    if a.finetune_epochs > 0:                             # fine-tune the top of MobileNetV2 with a tiny learning rate
        base.trainable = True
        for layer in base.layers[:-30]:
            layer.trainable = False
        model.compile(optimizer=keras.optimizers.Adam(1e-5), loss="sparse_categorical_crossentropy", metrics=["accuracy"])
        h2 = model.fit(train_ds, validation_data=val_ds, epochs=a.finetune_epochs, callbacks=[stop()])
        for k, v in h2.history.items():
            history[k] += list(v)

    OUT.mkdir(parents=True, exist_ok=True)
    model.save(OUT / "food_model.keras")
    names = [pretty(c) for c in class_names]
    (OUT / "class_names.json").write_text(json.dumps(names), encoding="utf-8")

    v_probs, v_true = predict_all(model, val_ds)
    t_probs, t_true = predict_all(model, test_ds)
    v_acc = float((v_probs.argmax(1) == v_true).mean()); t_acc = float((t_probs.argmax(1) == t_true).mean())
    thr = a.threshold if a.threshold is not None else choose_threshold(v_probs.max(1), v_probs.argmax(1) == v_true)
    (OUT / "config.json").write_text(json.dumps(
        {"threshold": thr, "val_accuracy": round(v_acc, 4), "test_accuracy": round(t_acc, 4), "classes": names}), encoding="utf-8")

    t_pred = t_probs.argmax(1)
    report = classification_report(t_true, t_pred, target_names=names, zero_division=0)
    (OUT / "classification_report.txt").write_text(report, encoding="utf-8")
    print(report)
    print(f"Validation accuracy {v_acc:.3f} | TEST accuracy {t_acc:.3f} | confirmation threshold {thr}")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    for i, m in enumerate(["accuracy", "loss"]):
        ax[i].plot(history[m], label="train"); ax[i].plot(history["val_" + m], label="validation")
        ax[i].set_title(m); ax[i].set_xlabel("epoch"); ax[i].legend()
    fig.tight_layout(); fig.savefig(OUT / "training_curves.png", dpi=150)
    cm = confusion_matrix(t_true, t_pred)
    fig, ax = plt.subplots(figsize=(8, 7)); ax.imshow(cm, cmap="Greens")
    ax.set_xticks(range(len(names)), names, rotation=45, ha="right"); ax.set_yticks(range(len(names)), names)
    for i in range(len(cm)):
        for j in range(len(cm)):
            ax.text(j, i, cm[i, j], ha="center", va="center", fontsize=8)
    ax.set_title("Confusion matrix (test set)"); fig.tight_layout(); fig.savefig(OUT / "confusion_matrix.png", dpi=150)
    print("Saved model, charts and report in", OUT, "\nRestart run.bat and open /api/health: dl_model_loaded should be true.")


if __name__ == "__main__":
    main()
