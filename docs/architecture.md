# SmartPack AI - architecture

```
Browser (frontend/: HTML + CSS + JS, English / Hindi / Telugu)
   |  POST /api/detect-food (image)          POST /api/recommend (JSON)
   v
Flask backend (backend/)
   |-- services/dl_service.py  -> dl/predict_food.py      (MobileNetV2, optional)
   |-- services/pipeline.py    -> database lookup -> ml/predict_packaging.py (scikit-learn)
   |                              fallback: services/rules.py when no model is trained
   v
SQLite (default) or MySQL: foods, packaging_materials, predictions
```

## Data flow
1. Image -> DL model -> food name + probability (low probability -> user confirms).
2. Food name -> database -> reference properties (moisture, fat, pH, respiration).
3. Properties + user inputs (shelf life, storage, transport, temperature) -> ML model -> packaging.
4. Packaging id -> database -> specifications (OTR, WVTR, thickness, sealability, strength, MAP).
5. `rules.packing_guide()` adds a spoilage-risk level, packing steps, a travel-time tip and a temperature tip.
6. Result page shows item name, packaging, packing guide, why, storage, alternative and eco option.

## Honest limitations (put these in your report)
- Food properties and packaging specs are typical reference values, not measured from the photo.
- The ML dataset is rule-generated, so its accuracy mostly reflects the rules. Replace with expert data.
- Softmax probability is not calibrated confidence. Choose the threshold from validation results.
- Non-food images can still be mapped to a food class; Phase 1 relies on user confirmation.

## Still to build (from the plan)
Admin dashboard (/api/history already stores data), non-food detection, shelf-life prediction, React/Tailwind UI.
