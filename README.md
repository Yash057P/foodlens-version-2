# FoodLens v2 — Food Recognition on Food-101 with EfficientNetB0

Dish recognition with ingredient, calorie and allergen lookup — delivered as a
Flask web app (mobile-first UI) and a Docker image.

## Features
- Trained **EfficientNetB0** on the full **101-class Food-101** dataset.
- Measured Food-101 test metrics (25,250 held-out images): **Top-1 73.9%, Top-3 88.4%, Top-5 92.7%**.
- Confidence warnings and top-3 alternatives improve decision support, but do not change closed-set top-1 accuracy.
- `best_model.keras` (40 MB) ships with the app — no external model download needed.
- Flask API (`/api/predict`) + responsive web UI: live camera, gallery upload, drag-drop,
  top-3 probability bars, calories, ingredients, allergen alerts, warning policy.
- Deploy: Docker + Render blueprint.

## Quick start (local)
```bash
# Linux / macOS
python -m venv .venv
source .venv/bin/activate
pip install -r webapp/requirements-web.txt
KERAS_BACKEND=torch python webapp/app.py
```
```powershell
# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\activate
pip install -r webapp\requirements-web.txt
$env:KERAS_BACKEND="torch"
python webapp\app.py
```
Open http://localhost:5000. First startup takes ~1 minute (model + backend init).

## Full Food-101 retraining

The reproducible full-dataset recipe uses EfficientNetV2S, streams the official
Food-101 images from disk, reserves 10% of the official training images per class
for validation, and evaluates the untouched 25,250-image test split:

```bash
KERAS_BACKEND=tensorflow python scripts/train_food101_full.py \
  --epochs-frozen 8 \
  --epochs-finetune 12 \
  --batch-size 32
```

The best checkpoint and JSON metrics are written under `results/`. The output
model accepts raw RGB pixels in the same `[0,255]` range as the Flask inference
path. Replace `webapp/models/best_model.keras` only after reviewing the held-out
test metrics.

## API
`POST /api/predict` — multipart upload with field `image`.
Returns top-3 predictions with probabilities, ingredients, calories, allergens and warnings.

```json
{
  "status": "ok",
  "top": [
    { "rank": 1, "class": "pizza", "name": "Pizza", "prob": 0.95 }
  ],
  "warnings": [],
  "ingredients": { "calories": 480, "ingredients": ["dough", "tomato sauce", "mozzarella"], "allergens": ["gluten", "dairy"] }
}
```

Other endpoints: `GET /api/health`, `GET /api/classes`.

## Deploying to Render (free)
1. Push this repo to GitHub.
2. On dashboard.render.com: **New > Blueprint**, select the repo — it uses the included
   `render.yaml` (Docker web service, health check `/api/health`).
3. Render builds the Docker image (server-side Keras uses TensorFlow CPU) and serves HTTPS —
   the camera works on mobile automatically over HTTPS.

Alternative: **New > Web Service**, repo root, runtime Docker, plan Free.

## Project structure
```
├── webapp/
│   ├── app.py                    # Flask routes
│   ├── inference.py              # model loading + prediction + warnings
│   ├── data/                     # classes_101.json, ingredients.json
│   ├── models/best_model.keras   # trained EfficientNetB0
│   ├── templates/index.html      # web UI
│   └── static/                   # CSS + JS
├── src/                          # data prep, training, evaluation scripts
├── training_food101.ipynb        # training notebook (Kaggle/Colab)
├── Dockerfile
└── render.yaml                   # Render blueprint
```

## Disclaimer
Nutrition values are estimates per typical serving. Educational use only — not medical advice.

## License
MIT