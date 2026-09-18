"""Dataset preprocessing cache (Batch 7 core).

Decodes every manifest image once: RGB -> center-crop square -> resize 224 ->
uint8 [0,255], and memoizes (X, Y) numpy arrays to data/preprocessed/ so every
training run skips JPEG decoding. Y = class index from labels.json.

lookup order uses the manifest order, so labels stay aligned across runs.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
from PIL import Image

from config import DATA_DIR, IMAGE_DIR, MANIFESTS_DIR

PREPROCESSED_DIR = DATA_DIR / "preprocessed"
PREPROCESSED_DIR.mkdir(parents=True, exist_ok=True)

Image.MAX_IMAGE_PIXELS = None


def _labels() -> dict[str, int]:
    return json.loads((MANIFESTS_DIR / "labels.json").read_text(encoding="utf-8"))["name_to_index"]


def _process_one(img_path: Path, size: int = 224) -> np.ndarray:
    arr = np.asarray(Image.open(img_path).convert("RGB"), dtype=np.uint8)
    h, w = arr.shape[:2]
    s = min(h, w)
    y0, x0 = (h - s) // 2, (w - s) // 2
    arr = arr[y0:y0 + s, x0:x0 + s]
    return np.asarray(Image.fromarray(arr).resize((size, size), Image.BILINEAR), dtype=np.uint8)


def build_cache(size: int = 224) -> dict[str, tuple[int, int]]:
    labels = _labels()
    sizes = {}
    for split in ("train", "val", "test"):
        x_path = PREPROCESSED_DIR / f"{split}_x.npy"
        y_path = PREPROCESSED_DIR / f"{split}_y.npy"
        if x_path.exists() and y_path.exists():
            sizes[split] = (int(np.load(x_path, mmap_mode="r").shape[0]), len(labels))
            print(f"cache hit: {split} ({sizes[split][0]} imgs)", flush=True)
            continue
        rows = (MANIFESTS_DIR / f"{split}.csv").read_text(encoding="utf-8").splitlines()[1:]
        n = len(rows)
        x = np.empty((n, size, size, 3), dtype=np.uint8)
        y = np.empty((n,), dtype=np.int64)
        print(f"building cache: {split} ({n} imgs)", flush=True)
        for i, line in enumerate(rows):
            cls, rel = line.split(",")
            x[i] = _process_one(IMAGE_DIR / rel, size)
            y[i] = labels[cls]
            if i % 2000 == 0:
                print(f"  {split} {i}/{n}", flush=True)
        np.save(x_path, x)
        np.save(y_path, y)
        sizes[split] = (n, len(labels))
        print(f"  {split} done -> {x_path}", flush=True)
    return sizes


def load_cache(split: str):
    x = np.load(PREPROCESSED_DIR / f"{split}_x.npy")
    y = np.load(PREPROCESSED_DIR / f"{split}_y.npy")
    return x, y


if __name__ == "__main__":
    build_cache()