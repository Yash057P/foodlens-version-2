"""FoodLens v2 - shared configuration.

- TensorFlow/Keras API (Keras 3, PyTorch backend) - see README for rationale.
- 20-class subset used for the development baseline (results are not described
  as a full Food-101 benchmark; the shipped model is trained on all 101 classes).
- Stratified per-class split: 600 train / 150 val / 250 test (official test
  untouched during development).
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# ---------- paths ----------
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
EXTRACTED_DIR = DATA_DIR / "extracted"        # food-101/...
MANIFESTS_DIR = DATA_DIR / "manifests"
RESULTS_DIR = ROOT / "results"
MODELS_DIR = ROOT / "models"
FIGURES_DIR = RESULTS_DIR / "figures"

for _d in (RAW_DIR, EXTRACTED_DIR, MANIFESTS_DIR, RESULTS_DIR, MODELS_DIR, FIGURES_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# ---------- dataset ----------
ARCHIVE_URL = "https://data.vision.ee.ethz.ch/cvl/food-101.tar.gz"
ARCHIVE_PATH = RAW_DIR / "food-101.tar.gz"
ARCHIVE_SIZE_BYTES = 4_996_278_331          # verified via HTTP HEAD (Content-Range)
FOOD101_DIR = EXTRACTED_DIR / "food-101"
IMAGE_DIR = FOOD101_DIR / "images"
TRAIN_META = FOOD101_DIR / "meta" / "train.txt"
TEST_META = FOOD101_DIR / "meta" / "test.txt"

# ---------- experiment scope ----------
# Fixed 20-class subset. Diverse cuisines plus deliberately confusing pairs
# (hamburger/hot_dog, ramen/pho, dumplings/gyozas-style).
SUBSET_CLASSES = [
    "pizza", "sushi", "hamburger", "ramen", "ice_cream",
    "apple_pie", "french_fries", "fried_rice", "samosa", "chicken_curry",
    "pad_thai", "steak", "caesar_salad", "tiramisu", "hot_dog",
    "dumplings", "grilled_cheese_sandwich", "macaroni_and_cheese", "baklava", "pho",
]

# ---------- data pipeline ----------
IMG_SIZE = 224
VAL_PER_CLASS = 150          # from the 750 official train images
TRAIN_PER_CLASS = 600        # 750 - 150
TEST_PER_CLASS = 250         # official test split (never used until Batch 37)
SEED = 42

# ---------- training (provisional, Batch 11 freezes the protocol) ----------
BATCH_SIZE = 32
EPOCHS_PRETRAIN_FROZEN = 5
EPOCHS_FINETUNE = 15
EPOCHS_SCRATCH = 20
LEARNING_RATE = 1e-3
FINETUNE_LR = 1e-5
DROPOUT = 0.3
PATIENCE = 3

# ---------- warning threshold (selected on validation in Batch 35) ----------
WARNING_THRESHOLD = 0.5     # provisional; finalized from validation data only