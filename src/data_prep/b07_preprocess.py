"""Batch 7 - Preprocessing: contract + channel statistics.

Every image is decoded to RGB, aspect-preserved center-crop to a square, resized
to IMG_SIZE (224), producing float32 arrays in [0, 255] - see DataSet.loaders.
Backbone-specific scaling (preprocess_input) is applied per model in Module 2.

This batch measures per-channel mean/std (pre-tensorized view over a sample) and
writes results/preprocess/statistics.json. Full per-image pipeline validation is
performed by b10_validate.
"""
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
from PIL import Image

from config import IMAGE_DIR, MANIFESTS_DIR, RESULTS_DIR, IMG_SIZE, SEED

PP_DIR = RESULTS_DIR / "preprocess"
PP_DIR.mkdir(parents=True, exist_ok=True)

N_SAMPLE = 2000


def main() -> None:
    lines = (MANIFESTS_DIR / "train.csv").read_text(encoding="utf-8").splitlines()[1:]
    rng = random.Random(SEED)
    rows = rng.sample(lines, min(N_SAMPLE, len(lines)))

    means, stds = [], []
    for line in rows:
        rel = line.split(",")[1]
        img = Image.open(IMAGE_DIR / rel).convert("RGB")
        arr = np.asarray(img, dtype=np.float32)
        h, w = arr.shape[:2]
        s = min(h, w)
        y0, x0 = (h - s) // 2, (w - s) // 2
        arr = arr[y0:y0 + s, x0:x0 + s]
        arr = np.asarray(Image.fromarray(arr.astype(np.uint8)).resize((IMG_SIZE, IMG_SIZE), Image.BILINEAR), dtype=np.float32)
        means.append(arr.reshape(-1, 3).mean(axis=0))
        stds.append(arr.reshape(-1, 3).std(axis=0))

    m = np.mean(means, axis=0)
    s = np.mean(stds, axis=0)
    out = PP_DIR / "statistics.json"
    out.write_text(json.dumps({"sample": N_SAMPLE, "channels": "RGB", "mean": m.tolist(), "std": s.tolist()}, indent=2), encoding="utf-8")
    print(f"sample={N_SAMPLE} per-channel mean={m.round(2).tolist()} std={s.round(2).tolist()}", flush=True)
    print("statistics ->", out, flush=True)


if __name__ == "__main__":
    main()