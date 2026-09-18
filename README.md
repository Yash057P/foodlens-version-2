# FoodLens v2 - Food recognition on Food-101 with EfficientNetB0

DLProjectSynopsis project (Sem VII 2026-27).
Dish recognition + ingredient/nutrition lookup + allergen warnings, delivered as a
Flask web app (mobile-first UI) and a Docker image.

## Highlights
- Trained **EfficientNetB0** on the full **101-class Food-101** dataset (Kaggle/Colab).
- Test metrics (25,250 held-out images): **Top-1 73.9%, Top-3 88.4%, Top-5 92.7%**.
- `best_model.keras` (40 MB) ships with the app - no external model download needed.
- Flask API (`/api/predict`) + responsive web UI: live camera, gallery upload, drag-drop,
  top-3 probability bars, calories, ingredients, allergens, warning policy.
- Local dev: Keras 3 with PyTorch backend (`KERAS_BACKEND=torch`) on RTX 3050 4 GB.
- Deploy: Docker + Render blueprint.

## Quick start (local)
```powershell
cd C:\Users\Yash\Desktop\Yash\DL\foodlens2
.venv\Scripts\activate
pip install -r webapp\requirements-web.txt
$env:KERAS_BACKEND="torch"
python webapp\app.py
# open http://localhost:5000
```
First startup takes ~1 min (model + CUDA init). Dev server default, good locally.

## Deploying to Render (free)
1. Push this repo to GitHub (repo: `foodlens-version-2`).
2. On dashboard.render.com: **New > Blueprint**, pick the repo, follow the included
   `render.yaml` (Docker web service, health check `/api/health`).
3. Render builds the Docker image (Keras server-side is TF-CPU) and serves HTTPS.
   Camera works over HTTPS automatically.
Alternative: **New > Web Service** with repo root, runtime Docker, plan Free.
