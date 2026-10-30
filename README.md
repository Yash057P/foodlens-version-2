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

## Viva-ready Docker demo

Build, start, health-check, and browser-test the complete application with one
PowerShell command:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\verify_docker.ps1
```

Open http://localhost:5000 and select **Viva mode** for a five-step explanation
of preprocessing, EfficientNetB0 feature extraction, TTA aggregation, confidence
rails, and the deterministic nutrition lookup. The container uses Gunicorn,
warms the model before reporting ready, and exposes Docker health status through
`/api/health`.

To choose reliable real photographs for the demonstration, place candidate
images in a local folder and rank them with the running model:

```powershell
python scripts\select_viva_samples.py C:\path\to\food-photos
```

Twelve neutral-filename Food-101 validation images are retained under
`webapp/static/demo-food101/` for manual viva uploads. Their private labels,
source rows, and hashes are recorded in `docs/FOOD101_DEMO_SAMPLES.md`.

Visually verify every suggested label. Use one clear high-confidence photograph
for the successful classification and one difficult or non-food image to explain
the low-confidence and ambiguity warnings.

## Personalized and continuously improving

- **Food profile:** locally stores selected allergy concerns and diet preferences,
  then highlights possible conflicts from the reference ingredient entry.
- **Correction loop:** saves confirmed or corrected Food-101 labels to the
  persistent `foodlens-feedback` Docker volume. Photo retention is explicit,
  optional, and off by default. Opted-in samples can be exported for human review.
- **Nearby discovery:** opens a Maps search for the predicted dish and lets the
  user compare third-party restaurant ratings.

These are decision-support features. FoodLens cannot verify allergens, recipe
composition, cross-contact, or medical suitability from an image. See
`docs/ENHANCEMENT_ROADMAP.md` for the scoped enhancement classification.

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

Other endpoints: `GET /api/health`, `GET /api/classes`, `GET /api/evaluation`,
`POST /api/explain`, `POST /api/compare-tta`, and `POST /api/feedback`.

## Viva-focused deep-learning evidence

The web app now exposes Grad-CAM explanations, normalized prediction entropy,
top-1 margin, configurable confidence threshold, single-view versus 3-view TTA,
image-quality checks, and a downloadable prediction report. The Model Evaluation
page presents held-out Food-101 metrics, weakest classes, confusion pairs, and the
stored TTA ablation with provenance.

Supporting workflows:

```powershell
python scripts\export_feedback.py --feedback path\to\feedback.jsonl
python scripts\calibrate_temperature.py --predictions data\preprocessed\food101_preds.npz
python scripts\benchmark_architectures.py --runs 5
python scripts\quantize_model.py --model webapp\models\best_model.keras
```

Temperature calibration was fitted from 11,363 seeded development predictions
generated on Kaggle and evaluated on the untouched 25,250-image official test
split. Live probabilities use scalar temperature 1.350; test ECE fell from 4.47%
to 3.57% and NLL from 0.995 to 0.973. The cost benchmark uses random
weights and compares engineering cost only, never accuracy.
The current mixed-precision EfficientNet graph also requires converter work before
standard TFLite FP16 export succeeds.

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
