# SmartPack AI

Upload a food image → the system identifies the food (e.g. **Potato Chips**) → you enter shelf life, storage type, **travel time (hours)** and temperature → ML recommends packaging → the result page shows the item name, packaging specs, a **spoilage risk and step-by-step packing guide** (for fruits, vegetables, potato chips and bread, tuned to your travel time and temperature), why, alternatives and a sustainable option.

The website supports **English, हिन्दी and తెలుగు** (language switch at the top right).

## Project structure

```
smartpack-ai/
├── setup.bat            one-time setup (Windows)
├── run.bat              start the website (Windows)
├── frontend/            website (HTML + CSS + JS, 3 languages)
│   ├── index.html
│   ├── css/style.css
│   └── js/ (app.js, i18n.js)
├── backend/             Flask API (also serves the frontend)
│   ├── app.py
│   ├── config/ routes/ services/ models/ utils/
│   ├── requirements.txt
│   └── .env.example
├── ml/                  packaging recommendation (scikit-learn)
│   ├── generate_dataset.py  train_model.py  predict_packaging.py
├── dl/                  food image classifier (TensorFlow/Keras, MobileNetV2)
│   ├── train_model.py  predict_food.py  threshold.py  train_on_colab.ipynb
├── database/            schema.sql (MySQL) + reference_data.py
├── train_dl.bat         build dataset + train the photo model (Windows)
├── datasets/
│   ├── prepare_dataset.py           builds images/ from the real datasets
│   ├── images/<10 food folders>/    put your photos here (apple, banana, ..., potato_chips, bread)
│   └── ml/                          generated packaging CSV
├── online/smartpack-ai-online.html   single-file version for hosting / sharing (no server)
└── docs/architecture.md
```

## 1. Requirements

- **Python 3.10 – 3.12** (tick *Add Python to PATH* when installing)
- VS Code (optional): **File → Open Folder → smartpack-ai**

## 2. Quick start (Windows cmd)

Unzip, then in `cmd`:

```cmd
cd path\to\smartpack-ai
setup.bat
run.bat
```

Open **http://localhost:5000**. That is all you need for the website, the ML model and the database.

### Same thing, step by step

```cmd
cd smartpack-ai
python -m venv venv
venv\Scripts\activate
pip install -r backend\requirements.txt
python ml\generate_dataset.py
python ml\train_model.py
cd backend
python app.py
```

macOS / Linux: use `source venv/bin/activate` and `/` in paths.

In VS Code you can run the same commands in **Terminal → New Terminal**.

## 3. Check each part separately

```cmd
python ml\predict_packaging.py --food Tomato --shelf-life 12 --storage Chilled --transport Long --temp 5
curl http://localhost:5000/api/health
```

`/api/health` shows whether the DL and ML models are loaded and which database is used.

## 4. Real dataset + food-photo model (deep learning)

Until you train this, the website runs in **demo mode** (file-name guess, or you pick the food from the dropdown).

**Which data to use** (checked against the dataset pages; I could not download them from my sandbox, so verify the folders on your PC):

| Classes | Source | Notes |
|---|---|---|
| apple, banana, carrot, mango, onion, orange, potato, tomato | Kaggle **Fruit and Vegetable Image Recognition** (`kritikseth/fruit-and-vegetable-image-recognition`) | about 100 train + 10 test + 10 validation images per class, scraped from Bing, educational use |
| bread | **Food-11** (Kaggle `vermaavi/food11`, or EPFL MMSPG), class *Bread* | thousands of images; the script keeps 150 |
| potato_chips | **no ready-made dataset found** | download from the web with the script below and/or add your own photos |

`potato` stays as a class on purpose: it teaches the model to tell whole potatoes from potato chips.

**Steps (cmd, from the project folder):**

```cmd
venv\Scripts\activate
pip install -r dl\requirements.txt

REM 1. Download (Kaggle account + token saved as %USERPROFILE%\.kaggle\kaggle.json), or download in the browser and unzip into these folders
kaggle datasets download -d kritikseth/fruit-and-vegetable-image-recognition -p downloads\fruitveg --unzip
kaggle datasets download -d vermaavi/food11 -p downloads\food11 --unzip

REM 2. Build datasets\images (converts to clean JPEG, caps 150 per class)
python datasets\prepare_dataset.py --fruitveg downloads\fruitveg --food11 downloads\food11 --max-per-class 150

REM 3. Potato chips: download from the web, THEN open datasets\images\potato_chips and delete wrong pictures
python datasets\prepare_dataset.py --download potato_chips --count 150 --max-per-class 150

REM 4. Check, train, test
python datasets\prepare_dataset.py --check
python dl\train_model.py
python dl\predict_food.py path\to\tomato.jpg
python dl\predict_food.py --folder path\to\my_photos
```

`train_dl.bat` runs steps 2, 4 (check + train) for you once the downloads exist. No fast PC? Use the free GPU in Google Colab: upload `dl\train_on_colab.ipynb` (untested notebook, same steps).

Then restart `run.bat`; `http://localhost:5000/api/health` should show `"dl_model_loaded": true`. The website now identifies the food from the photo. If the top probability is below the threshold (chosen automatically from the validation set, see `dl\models\config.json`) the page asks the user to confirm.

**What training produces** in `dl\models\`: `food_model.keras`, `class_names.json`, `config.json` (threshold, validation/test accuracy), `classification_report.txt`, `training_curves.png`, `confusion_matrix.png`. Use these in your report.

**Be realistic about accuracy**
- The test score comes from the same web-scraped sources as the training data, so it will look better than real life.
- Test with **your own phone photos** (`--folder` command above). Expect lower accuracy on those, especially for potato chips (few, noisy web images) and bread (Food-11 bread is very varied).
- To improve results: add 50-100 of your own photos per class (different backgrounds and lighting), delete wrong images, and retrain.
- No model is always right. The confirm step for low-probability photos stays important.
- If loading the model fails with a Keras/TensorFlow version error, train and run with the same TensorFlow version (`pip install -U tensorflow`).

**Travel time:** under 6 h = short, 6–24 h = medium, over 24 h = long. The packing guide and the ML model both use this.
The spoilage-risk level and packing tips come from simple rules (`backend/services/rules.py`) and typical temperature ranges, not from a trained model, so check them against food-packaging references before presenting them as expert advice.

## 5. MySQL (optional)

SQLite is the default and needs no setup. To use MySQL:

```cmd
mysql -u root -p < database\schema.sql
copy backend\.env.example backend\.env
```

Edit `backend\.env`: set `DB_TYPE=mysql` and your `MYSQL_*` values, then run again. MySQL support is written but I could not test it against a live MySQL server, so check it on your machine.

## 6. API

| Method | URL | Purpose |
|---|---|---|
| POST | `/api/detect-food` | multipart field `image` → food + probabilities |
| POST | `/api/recommend` | JSON `{food, shelf_life, storage_type, travel_hours, temperature}` → full result incl. `guide` (spoilage risk + packing steps) |
| GET | `/api/food/<name>` | food reference properties |
| GET | `/api/packaging/<id>` | packaging specifications |
| GET | `/api/foods` | supported foods |
| GET | `/api/history` | stored recommendations |
| GET | `/api/health` | status |

## 7. Single-file online version

`online\smartpack-ai-online.html` is the whole website in one file (all 3 languages, packing guide, item names). Double-click it to open in a browser, or upload it to any static host (Netlify, GitHub Pages). It has **no Flask backend and no trained ML model**: the packaging choice comes from the same rules as `backend/services/rules.py`, and food detection is a file-name guess you confirm. The copy shared on claude.ai also asks Claude to recognise the photo; that part only works inside claude.ai.

## 8. Share it for a short time

`localhost` works only on your computer. To let others open it temporarily, keep `run.bat` running and, in another cmd window:

```cmd
npx localtunnel --port 5000
```

(or use ngrok / Cloudflare Tunnel). Share the link it prints, and close the window to stop sharing.

## 9. Be honest about these (viva)

- Food properties and packaging values (OTR, WVTR, thickness) are **typical reference values**, not measured from the photo. Check them against published sources.
- The ML dataset is **rule-generated** (`ml/generate_dataset.py`), so the ~100% accuracy mostly shows the model learned the rules. Replace or extend it with expert/literature-based data and say so in your report.
- Softmax probability is **not calibrated confidence**; the confirm threshold is picked from validation data.
- The photo model's accuracy depends on the datasets (web-scraped, educational use). Cite them, and report accuracy on your own photos too.
- A non-food image may still be mapped to a food class; for now the user confirms the food.
- The spoilage-risk level and packing tips are rule-based and approximate.
- Hindi and Telugu text is machine-written: get it checked by a native speaker.

## Troubleshooting

- **`python` not recognised**: reinstall Python with *Add to PATH*, or try `py` instead of `python`.
- **Port 5000 busy**: set `PORT=5001` in `backend\.env`.
- **TensorFlow will not install**: use Python 3.10–3.12 (a 64-bit build). The website works without TensorFlow.
- **Page shows old text**: hard refresh with Ctrl+F5.
