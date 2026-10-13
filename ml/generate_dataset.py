"""
Generate a SYNTHETIC packaging dataset -> datasets/ml/packaging_dataset.csv

WARNING (read before your viva): the labels are produced by the rules in
backend/services/rules.py, so a model trained on this file mostly re-learns those
rules and will score very high. That accuracy does NOT prove real-world performance.
Replace or extend this CSV with expert-labelled / literature-based rows when you can,
and describe the data honestly as "rule-generated" in your report.

Usage:  python ml/generate_dataset.py [--rows 4000] [--seed 42]
"""
import argparse
import random
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from database.reference_data import FOODS, PACKAGING          # noqa: E402
from backend.services.rules import rule_based_packaging       # noqa: E402

SHELF_RANGE = {"Potato Chips": (30, 180), "Bread": (2, 10)}           # days; default (2, 30)
TEMP_RANGE = {"Ambient": (15, 30), "Chilled": (0, 10), "Frozen": (-25, -15)}


def pick_storage(food, rng):
    if food == "Potato Chips":
        return "Ambient"
    frozen_chance = 0.10 if food == "Bread" else 0.08
    r = rng.random()
    if r < frozen_chance:
        return "Frozen"
    return rng.choice(["Ambient", "Chilled", "Chilled"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", type=int, default=4000)
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    rng = random.Random(a.seed)

    rows = []
    names = list(FOODS)
    for _ in range(a.rows):
        food = rng.choice(names)
        f = FOODS[food]
        lo, hi = SHELF_RANGE.get(food, (2, 30))
        life = rng.randint(lo, hi)
        storage = pick_storage(food, rng)
        transport = rng.choice(["Short", "Medium", "Long"])
        t_lo, t_hi = TEMP_RANGE[storage]
        temp = round(rng.uniform(t_lo, t_hi), 1)
        pid = rule_based_packaging(food, f["respiration"], life, storage, transport)
        rows.append({
            "food_name": food,
            "moisture_level": f["moisture"],
            "fat_level": f["fat"],
            "ph_category": f["ph"],
            "respiration_level": f["respiration"],
            "required_shelf_life": life,
            "storage_type": storage,
            "storage_temperature": temp,
            "transportation_type": transport,
            "packaging_material": PACKAGING[pid]["name"],
        })

    out = ROOT / "datasets" / "ml" / "packaging_dataset.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    df.to_csv(out, index=False)
    print(f"Saved {len(df)} rows -> {out}")
    print(df["packaging_material"].value_counts().to_string())


if __name__ == "__main__":
    main()
