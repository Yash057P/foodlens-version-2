# FoodLens — Complete Project Content

**Smart Food Recognition Using Deep Learning with Top-3 Predictions and
Ingredient Information**

Department of Information Technology — Deep Learning Lab Project (Sem VII),
Academic Year 2026–27. Project Guide: Dr. Sushopti Gawade.

**Team**
| Sr. No. | Full Name        | Roll Number |
|---------|------------------|-------------|
| 1       | Sarthak Kulkarni | 23101B0019  |
| 2       | Harshad Patekar  | 23101B0026  |
| 3       | Tanay Shinde     | 23101B0034  |
| 4       | Yash Patil       | 23101B0060  |

**Hypothesis (from the synopsis)**
> Under a common data split and training budget, at least one ImageNet-pretrained
> convolutional neural network will achieve higher held-out food-classification
> accuracy than a custom CNN trained from scratch. This hypothesis will be
> tested experimentally, not assumed to be true.

Cross-reference between this document and the deliverables:
- IEEE paper: [`paper/main.tex`](main.tex) (LaTeX, IEEEtran conference format)
- References: [`paper/references.bib`](references.bib)
- Generated figures: [`paper/figures/`](figures/)
- Generated LaTeX tables: [`paper/tables/`](tables/)

---

## 1. Project Overview

FoodLens identifies the dominant food dish in an uploaded photograph and
returns its *three highest-scoring* food categories with their model scores.
Five deep learning architectures are compared on the Food-101 benchmark under
one consistent, reproducible protocol. The selected model is integrated into a
web application that visualises scores, flags low-confidence predictions, and
retrieves curated dish–ingredient information.

Key design principle — **prediction is separated from information**:
- *Prediction*: produced by the trained neural network from image pixels.
- *Ingredient information*: a manually curated lookup (common recipe
  ingredients), never described as "ingredients detected from the image".

Contribution: **integration and reproducible evaluation**, not a new neural
architecture and not a medical/nutrition tool.

### Problem Statement
Given one RGB photograph containing a dominant food item, predict its category
from a fixed set of supported classes and present clearly qualified
information about the prediction. The system must not present recipe-level
ingredients as image-verified facts.

### Objectives
1. Prepare a reproducible Food-101 training, validation, and test pipeline.
2. Implement and compare at least five deep learning architectures.
3. Display the Top-3 predictions, model scores, and low-score warnings.
4. Retrieve curated common ingredients for supported predicted dishes.
5. Deliver a web demonstration, evaluation report, and documented limitations.

---

## 2. Literature Review (Related Work)

Papers used as literature evidence (results are *not* reproduced here):

1. **Suddul & Seguin (2023)** — *A comparative study of deep learning methods
   for food classification with images*, Food and Humanity 1, pp. 800–808.
   Compares a CNN trained from scratch with transfer learning; uses
   augmentation and EfficientNetV2 on 11 food groups. Supports the
   baseline-versus-transfer design (not a 101-class evaluation). DOI:
   `10.1016/j.foohum.2023.07.018`.
2. **Abiyev & Adepoju (2024)** — *Automatic Food Recognition Using Deep
   Convolutional Neural Networks with Self-attention Mechanism*,
   Human-Centric Intelligent Systems 4, pp. 171–186. Combines CNNs and
   self-attention with averaged ensemble predictions; evaluates on Food-101 and
   MA Food-121. Motivates confusing-class analysis; attention/ensembles are out
   of core scope here. DOI: `10.1007/s44230-023-00057-9`.
3. **Razia Sulthana, Tilford & Stoyanov (2024)** — *Fine-grained food image
   classification and recipe extraction using a customized deep neural network
   and NLP*, Computers in Biology and Medicine 175, 108528. Uses a customized
   MResNet-50 plus NLP with a domain ontology for ingredients/recipes.
   Motivates a *separate information layer*; our curated lookup does not
   reproduce its NLP pipeline. DOI: `10.1016/j.compbiomed.2024.108528`.
4. **Food-101 (Bossard, Guillaumin & Van Gool, ECCV 2014)** — the dataset used
   in this project. DOI: `10.1007/978-3-319-10599-4_29`.

Also referenced: Torchvision Food101 documentation (dataset-structure
verification), Keras Applications documentation (pretrained model backbones),
and Guo et al. (ICML 2017) on calibration of neural-network scores.

---

## 3. Dataset — Food-101

Source (official): https://data.vision.ee.ethz.ch/cvl/datasets_extra/food-101/

| Parameter | Value |
|-----------|-------|
| Number of classes | 101 |
| Images per class | 1,000 |
| Official training images/class | 750 |
| Official test images/class | 250 |
| Project training images/class (development subset) | 600 |
| Project validation images/class (development subset) | 150 |
| Test images/class | 250 |
| Input size | 224 × 224 × 3 (RGB) |

Facts:
- Training images intentionally include some noise (including incorrect
  labels).
- Images have a maximum side length of 512 pixels.
- Validation is created **only from the official training images** (fixed
  seed 42); the official test set stays untouched until final evaluation.

### Partitions used
Two tracks were used and both are documented in the paper:
1. **Development subset (20 classes)** — per-class 600/150/250 split,
   manifests produced and validated:
   `data/manifests/train.csv` (12,000 rows), `val.csv` (3,000),
   `test.csv` (5,000). All Module-1 checks passed (class membership,
   disjointness, determinism, loader shapes).
2. **Full 101-class production run (EfficientNetB0)** — global random 85/15
   split of the official training set ≈ 63,750 train / 11,250 validation;
   official 25,250-image test set evaluated exactly once at the end.

> Note: the per-class 600/150 scheme is the synopsis plan; the full 101-class
> run used an 85/15 global split. Both facts are stated explicitly in the
> paper; nothing is silently altered.

### Data audit (Module 1, development subset)
`results/audit/audit.json`: 20,000 files checked, 0 corrupt, 1 grayscale
(`L`) image (converted to RGB), no tiny/huge images; dominant width 512 px
(17,201 files). Channel statistics over a 2,000-image sample in
`results/preprocess/statistics.json` (RGB mean ≈ [140.6, 113.2, 83.8]).

---

## 4. Data Preprocessing and Augmentation

- RGB conversion (grayscale images converted to RGB).
- Resize to 224 × 224.
- Backbone-specific preprocessing is wired per model
  (`keras.applications.*.preprocess_input`) where required. The recorded
  full-run notebook instead fed raw float32 pixels in [0,255] after JPEG
  decode + bilinear resize (documented deviation).
- **Training-only augmentation** (label-preserving): random horizontal flip,
  random rotation (±0.1 rad), random zoom (factor 0.1).
- **Validation/test preprocessing is deterministic**; no augmentation.

---

## 5. The Five Algorithms (Implemented)

All five solve the same 101-class classification problem. The four pretrained
backbones come from Keras Applications with ImageNet weights, original
classifier removed, and the project head attached:
`GAP → Dense(128, ReLU) → Dropout(0.3) → Dense(101, Softmax)`.
Models are *alternatives*; they are **not ensembled**.

| # | Algorithm | Role / notes |
|---|-----------|--------------|
| 1 | **Custom CNN** | Baseline, trained from random initialization. Three Conv2D(3×3)–ReLU–MaxPool blocks with 32/64/128 filters → GAP → Dense(128, ReLU) → Dropout(0.3) → Dense(101, Softmax). |
| 2 | **ResNet50** | Residual shortcut connections; pretrained feature extraction. |
| 3 | **MobileNetV2** | Inverted residuals + depthwise convolutions; accuracy–latency trade-off. |
| 4 | **DenseNet121** | Dense connectivity; feature reuse vs. residual learning. |
| 5 | **EfficientNetB0** | Balanced compound scaling; chosen as the deployed model in the current prototype. |

Classification head math (loss):
`p_c(x) = exp(z_c) / Σ_{j=1..101} exp(z_j)`,  `L(x,y) = −log p_y(x)`.

### Initial training configuration (synopsis)
| Setting | Value |
|---------|-------|
| Optimizer | Adam |
| Batch size | 32 (production run documented at 16) |
| Initial LR | 1e-3 |
| Transfer: frozen-backbone epochs | up to 5 (production: 10-head stage) |
| Transfer: fine-tuning epochs | up to 15 (production: fine-tune stage) |
| Fine-tuning LR | 1e-5 |
| Custom CNN epochs | up to 20 |
| Early stopping | monitor val loss (production also val acc), patience 3, restore best |
| Dropout | 0.3 |
| Random seed | 42 |

### Documented modifications (not silent changes)
- Production batch size 16 (memory), mixed `float16` precision.
- Phase 1: frozen backbone, Adam 1e-3, checkpoint on val accuracy.
- Phase 2: last ~20 backbone layers unfrozen, Adam 1e-5, early stopping
  patience 2 + `ReduceLROnPlateau`.
- Full-run input preprocessing: raw pixels, no extra normalization.

---

## 6. Actual Experiment Results

**Completed:** full 101-class training for EfficientNetB0
(`training_food101.ipynb`, deployed as `best_model.keras`).

**Held-out test evaluation** — official Food-101 test set, 25,250 images
(source: `results/food101_eval.json` + metrics computed from the saved
prediction cache `data/preprocessed/food101_preds.npz`; script
`scripts/analyze_food101.py`):

| Metric | Value |
|--------|-------|
| Test set size | 25,250 |
| **Top-1 accuracy** | **73.85 %** |
| **Top-3 accuracy** | **88.44 %** |
| Top-5 accuracy | 92.65 % |
| Macro precision | 73.82 % |
| Macro recall | 73.85 % |
| Macro F1-score | 73.74 % |
| Model file size | ≈ 42.24 MB (42,240,565 bytes) |
| Total parameters | 4,226,568 |
| Trainable parameters | 1,016,341 (fine-tuned state; probabilistic from serialized architecture) |
| Inference time | ≈ 6.6 ms/image, batched forward pass (batch 64) on evaluation machine |

Per-class details: `paper/tables/classification_report_full.txt` and
`paper/tables/table_per_class.tex` (top-15 / bottom-15).

**Best classes** (per-class accuracy): edamame 98.8 %, pho 92.4 %,
spaghetti_carbonara 91.6 %, onion_rings 91.6 %, macarons 91.2 %, oysters
90.8 %, miso_soup 90.4 %, hot_and_sour_soup 90.4 %, french_fries 90.4 %,
guacamole 89.6 %.

**Worst classes**: foie_gras 42.8 %, steak 45.6 %, apple_pie 46.0 %,
pork_chop 47.6 %, ceviche 48.4 %, ravioli 49.6 %, bread_pudding 51.2 %,
huevos_rancheros 53.2 %, chocolate_mousse 54.0 %, filet_mignon 54.0 %.

**Most confused pairs** (true → predicted, test counts): steak→filet_mignon
46, filet_mignon→steak 39, chocolate_cake→chocolate_mousse 30,
pork_chop→filet_mignon 27, tuna_tartare↔beef_tartare 26 each,
pulled_pork_sandwich→hamburger 25, cheesecake→strawberry_shortcake 23,
apple_pie→bread_pudding 23, ramen→pho 22, bruschetta→caprese_salad 22,
steak→prime_rib 21. These reflect genuine visual similarity.

**Smoke runs (Batch 13)** — one-epoch feasibility checks on the 20-class
dev subset (16 training batches): CustomCNN 95,828 params / 7.8 s; ResNet50
23,628,692 / 219.2 s; MobileNetV2 2,283,604 / 185.2 s; DenseNet121 7,058,004 /
657.1 s; EfficientNetB0 4,075,191 / 244.3 s (`results/smoke_log.txt`).
These are debugging runs, not benchmark comparisons.

---

## 7. Model Selection

- Synopsys rule: select by **validation Top-1 accuracy**, inference time as
  tie-breaker; freeze the model, preprocessing, class mapping, threshold, and
  evaluation configuration before test evaluation.
- The full five-way validation comparison is **pending** (only EfficientNetB0
  has a full 101-class run). In the delivered prototype, EfficientNetB0 was
  selected as the deployment model for product-oriented reasons recorded in
  the training notebook: fast inference, small model, low latency/memory, easy
  Docker/Render deployment, good accuracy.
- To date the **test set has not been used for any development decision**
  (split, hyperparameters, threshold, or model choice).

### Hypothesis status
The hypothesis requires the from-scratch Custom CNN baseline under the same
split/budget. That baseline has not yet completed a full 101-class run, so the
hypothesis is **not yet confirmed or rejected** by measured data. The paper
states this explicitly; it does not claim proof.

---

## 8. Warning (Low-Score) Policy

- If `max(model_score) < τ` → display *"Uncertain prediction—try a clearer
  image"* and **suppress ingredient suggestions**.
- Deployment rule uses τ = 0.45 (provisional; the synopsis requires a
  validation-selected threshold — validation-based selection is pending).
- Illustrated on held-out test predictions (illustrative only, not the
  selection set): at τ = 0.45 coverage ≈ 84.3 %, Top-1 on retained ≈ 81.9 %;
  at τ = 0.50 coverage ≈ 80.5 % / 83.8 %; at τ = 0.60 coverage ≈ 72.8 % /
  87.5 %.
- The warning is **not a validated food/non-food detector**; softmax scores
  are not guaranteed probabilities of correctness (cf. Guo et al.).

---

## 9. Ingredient Lookup

- Separate curated JSON knowledge base (`webapp/data/ingredients.json`),
  101 records (one per supported class).
- Record fields: common ingredients, category, calories per typical serving,
  allergen tags, recipe-variation note, source references.
- Described as *common recipe ingredient information*, **never** as
  "ingredients detected from the image".
- Suppressed for low-confidence predictions; missing entries return a fallback
  message.
- Disclaimer: nutrition values are estimates per typical serving, educational
  use only — not medical advice.

---

## 10. Web Application

Delivered as a lightweight web application: Flask backend
(`webapp/app.py`, `webapp/inference.py`) with a mobile-first HTML/CSS/JS front
end (`webapp/templates/index.html`, `webapp/static/`). Model
`webapp/models/best_model.keras` ships with the app (no external download).

Features: image upload validation, live camera / gallery upload, drag-drop,
Top-3 probability bars, low-confidence and ambiguity warnings, ingredients,
calories and allergen alerts, `/api/predict`, `/api/classes`, `/api/health`.
Dockerfile + `render.yaml` provided for Render deployment.

> The synopsis planned Streamlit; the delivered prototype's web layer is the
> Flask front end shipped in `foodlens2`. This implementation choice is noted
> and documented. The Streamlit variant remains an optional deliverable.

---

## 11. Results, Checkpoints, and Reproducibility

- Checkpoints: `models/*_smoke.keras` (20-class heads),
  `best_model.keras` (full, deployed), `webapp/models/best_model.keras`.
- Results: `results/food101_eval.json`, `results/food101_metrics.json`,
  `results/smoke_log.txt`, `results/audit/audit.json`,
  `results/preprocess/statistics.json`, `results/figures/`,
  `results/training/*_smoke_history.csv`.
- Cached test tensors/predictions: `data/preprocessed/*.npz`.
- Manifests: `data/manifests/{train,val,test}.csv`, `labels.json`,
  `module1_report.txt`.
- Configuration: `config.py` (paths, split params, seed 42, training protocol).
- Metadata (TF/Keras/Python versions, GPU) is recorded in experiment metadata
  JSON alongside package versions.
- Fixed random seed so splits and loaders are reproducible.

---

## 12. How to Run (Command Reference)

Create the environment and install dependencies, then:

```powershell
# Web application (Windows PowerShell)
$env:KERAS_BACKEND="torch"
python .venv\Scripts\python.exe webapp\app.py        # http://localhost:5000
# or equivalently, from the foodlens2 root:
.\.venv\Scripts\activate
$env:KERAS_BACKEND="torch"
python webapp/app.py
```

```bash
# Linux / macOS
python -m venv .venv && source .venv/bin/activate
pip install -r webapp/requirements-web.txt
KERAS_BACKEND=torch python webapp/app.py
```

Evaluation / metrics:
```bash
python scripts/analyze_food101.py    # recompute metrics + regenerate figures/tables
```

Full training on Food-101: run `training_food101.ipynb` (GPU recommended,
16 GB VRAM target; mixed float16; batch 16). The remaining four models must be
trained with the same split to complete the five-way comparison.

---

## 13. Compiling the IEEE Paper

From `paper/`:

```bash
pdflatex main
bibtex main
pdflatex main
pdflatex main
```

Requires `IEEEtran` class + `IEEEtran.bst` (included in all standard TeX
distributions and Overleaf). Packages used: cite, amsmath, amssymb, amsfonts,
graphicx, textcomp, booktabs, xcolor, fontenc, tikz.

---

## 14. Limitations (as stated in the paper)

- Single-label classification; no multi-dish detection, no segmentation.
- No calorie / portion-size / freshness / allergen estimation (calorie values
  are approximate per-serving estimates only).
- Ingredient lookup is curated recipe information, not image-level detection.
- Unsupported dishes and non-food objects can still receive high scores
  (closed-set, no rejection training).
- Scores must not be treated as guaranteed probabilities (limited calibration).
- Food-101 domain differs from arbitrary real-world images.

---

## 15. References (IEEE)

1. Suddul & Seguin, *A comparative study of deep learning methods for food
   classification with images*, Food and Humanity, vol. 1, pp. 800–808, 2023.
2. Abiyev & Adepoju, *Automatic Food Recognition Using Deep Convolutional
   Neural Networks with Self-attention Mechanism*, Human-Centric Intelligent
   Systems, vol. 4, pp. 171–186, 2024.
3. Razia Sulthana, Tilford & Stoyanov, *Fine-grained food image classification
   and recipe extraction using a customized deep neural network and NLP*,
   Computers in Biology and Medicine, vol. 175, art. 108528, 2024.
4. Bossard, Guillaumin & Van Gool, *Food-101 — Mining Discriminative
   Components with Random Forests*, ECCV, pp. 446–461, 2014.
5. PyTorch Contributors, *Food101 dataset implementation*, Torchvision
   documentation, 2026 (dataset-structure verification only).
6. Keras Contributors, *Keras Applications*, 2026 (pretrained backbones).
7. Guo, Pleiss, Sun & Weinberger, *On Calibration of Modern Neural Networks*,
   ICML, PMLR vol. 70, pp. 1321–1330, 2017.

Full machine-readable entries: `paper/references.bib`.

---

## 16. Final Checklist — Current Status

| Item | Status |
|------|--------|
| Food-101 pipeline works | ✅ (20-class dev validated; full run executed for ENetB0) |
| 600/150/250 split per class | ✅ for 20-class dev subset (design rule; see note on full run) |
| Five models implemented | ✅ (all built + smoke-verified) |
| Custom CNN trains from scratch | ✅ (built; full 101-class run pending) |
| Four pretrained use transfer learning | ✅ (built; full runs pending) |
| Same dataset split for all models | ⚠️ full-101 runs pending for 4 models |
| Training augmentation implemented | ✅ |
| Deterministic val/test preprocessing | ✅ |
| Checkpoints saved | ✅ (`models/*.keras`, `best_model.keras`) |
| Training curves saved | ✅ for smoke runs; full-run curves pending |
| Top-1 accuracy | ✅ 73.85 % (test) |
| Top-3 accuracy | ✅ 88.44 % (test) |
| Macro precision / recall / F1 | ✅ 73.82 / 73.85 / 73.74 % |
| Confusion matrices generated | ✅ (`figures/fig_confusion_full.pdf` etc.) |
| Model size measured | ✅ 42.24 MB |
| Parameter counts measured | ✅ total/trainable computed from serialized model |
| Training time measured | ✅ for smoke runs; full-run times pending |
| Inference time measured | ✅ ≈ 6.6 ms/img batched |
| Validation-based model selection | ⚠️ rule defined; five-way comparison pending |
| Warning threshold selected on validation only | ⚠️ deployed τ=0.45; validation-based selection pending |
| Test set untouched until final evaluation | ✅ (used once, for final evaluation) |
| Ingredient lookup + disclaimer | ✅ |
| Web application works | ✅ (Flask app; run command above) |
| IEEE LaTeX paper created | ✅ `paper/main.tex` |
| IEEE references created | ✅ `paper/references.bib` |
| Tables from actual experiment data | ✅ `paper/tables/*.tex` |
| Figures generated | ✅ `paper/figures/` |
| No fabricated results | ✅ all values sourced from recorded outputs |
| Paper compiles | ✅ (pdflatex + bibtex; verify on your TeX setup) |
| README | ✅ `foodlens2/README.md` |

## 17. Experiments Still to Run (Pending)

1. Full 101-class training of the Custom CNN baseline (required for the
   hypothesis test) under the same split/budget.
2. Full 101-class training of ResNet50, MobileNetV2, DenseNet121.
3. Validation-based comparison (Top-1 accuracy, macro F1) across the five
   models → fills Tables 3/4.
4. Validation-based warning threshold selection (coverage + retained
   accuracy on validation data).
5. Median single-image inference time after warm-up for all five models on the
   same documented device.
6. Persist full-run training/validation curves for the paper's training-curve
   figures.