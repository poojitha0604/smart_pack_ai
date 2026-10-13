"""
Train and compare packaging-recommendation models.

Compares Decision Tree, Random Forest, KNN and Logistic Regression, picks the best by
weighted F1 (ties broken by accuracy), and saves the full preprocessing + model
pipeline with joblib -> ml/models/packaging_model.joblib

Usage:  python ml/train_model.py
"""
import json
import sys
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, classification_report, confusion_matrix,
                             precision_recall_fscore_support)
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "datasets" / "ml" / "packaging_dataset.csv"
OUT = ROOT / "ml" / "models"

CATEGORICAL = ["food_name", "moisture_level", "fat_level", "ph_category", "respiration_level",
               "storage_type", "transportation_type"]
NUMERIC = ["required_shelf_life", "storage_temperature"]
TARGET = "packaging_material"


def main():
    if not DATA.exists():
        sys.exit(f"Dataset not found: {DATA}\nRun first:  python ml/generate_dataset.py")
    OUT.mkdir(parents=True, exist_ok=True)

    # keep_default_na=False: the level "None" (no respiration) must not be read as a missing value
    df = pd.read_csv(DATA, keep_default_na=False).replace("", pd.NA).dropna().drop_duplicates()   # 1. clean
    X, y = df[CATEGORICAL + NUMERIC], df[TARGET]
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    def make(model):                                             # 2. encode + scale
        pre = ColumnTransformer([
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
            ("num", StandardScaler(), NUMERIC),
        ])
        return Pipeline([("prep", pre), ("model", model)])

    candidates = {                                               # 3. train 4 models
        "Decision Tree": DecisionTreeClassifier(random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=200, random_state=42),
        "KNN": KNeighborsClassifier(n_neighbors=5),
        "Logistic Regression": LogisticRegression(max_iter=2000),
    }
    results, fitted = [], {}
    for name, model in candidates.items():                       # 4. compare
        pipe = make(model).fit(X_tr, y_tr)
        pred = pipe.predict(X_te)
        p, r, f1, _ = precision_recall_fscore_support(y_te, pred, average="weighted", zero_division=0)
        results.append({"model": name, "accuracy": round(accuracy_score(y_te, pred), 4),
                        "precision": round(p, 4), "recall": round(r, 4), "f1": round(f1, 4)})
        fitted[name] = pipe

    results.sort(key=lambda r: (r["f1"], r["accuracy"]), reverse=True)   # 5. choose by evaluation
    best = results[0]["model"]
    print(pd.DataFrame(results).to_string(index=False))
    print(f"\nBest model: {best}")

    best_pipe = fitted[best]
    joblib.dump(best_pipe, OUT / "packaging_model.joblib")       # 6. save pipeline
    pred = best_pipe.predict(X_te)
    report = classification_report(y_te, pred, zero_division=0)
    (OUT / "classification_report.txt").write_text(report, encoding="utf-8")
    (OUT / "model_comparison.json").write_text(
        json.dumps({"best": best, "results": results, "rows": len(df)}, indent=2), encoding="utf-8")
    print("\n" + report)

    try:                                                         # confusion matrix image (optional)
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        labels = sorted(y.unique())
        cm = confusion_matrix(y_te, pred, labels=labels)
        fig, ax = plt.subplots(figsize=(7, 6))
        ax.imshow(cm, cmap="Greens")
        ax.set_xticks(range(len(labels)), labels, rotation=45, ha="right", fontsize=7)
        ax.set_yticks(range(len(labels)), labels, fontsize=7)
        for i in range(len(labels)):
            for j in range(len(labels)):
                ax.text(j, i, cm[i, j], ha="center", va="center", fontsize=7)
        ax.set_title(f"Confusion matrix - {best}")
        fig.tight_layout()
        fig.savefig(OUT / "confusion_matrix.png", dpi=150)
    except Exception as e:  # noqa: BLE001
        print("Skipped confusion-matrix plot:", e)

    print(f"Saved model -> {OUT / 'packaging_model.joblib'}")


if __name__ == "__main__":
    main()
