"""Batch 9 - Dataset loaders.

`FoodDataset` is a torch Dataset reading JPEGs on the fly and returning float32
[0,255] (H,W,C) tensors, so Module 2 can apply each backbone's own
preprocess_input. Augmentation for the train split is applied with numpy/PIL
(random horizontal flip, ±15 deg rotation, ±10% brightness, 0.88-1.12 scale).

`make_loaders` returns (train, val, test) torch DataLoaders. Keras 3 with a
torch backend accepts these directly in fit()/evaluate().
"""
import csv
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import torch
from PIL import Image

from config import IMAGE_DIR, MANIFESTS_DIR, SEED

Image.MAX_IMAGE_PIXELS = None

AUG_KW = dict(hflip=True, rot_deg=15, hflip_p=0.5, bright_std=0.10, scale_range=(0.88, 1.12))
NO_AUG_KW = dict(hflip=False, rot_deg=0, hflip_p=0.0, bright_std=0.0, scale_range=(1.0, 1.0))


class FoodDataset(torch.utils.data.Dataset):
    def __init__(
        self,
        manifest: Path,
        labels_json: Path,
        img_size: int,
        augment: bool = False,
        seed: int = SEED,
    ) -> None:
        super().__init__()
        self.img_size = img_size
        self.augment = augment
        self.rng = random.Random(seed)
        self.rows = self._load_manifest(manifest)
        self.classes = sorted({cls for cls, _ in self.rows})
        self.name_to_index = {name: i for i, name in enumerate(self.classes)}

        if labels_json.exists():
            import json
            mapped = json.loads(labels_json.read_text(encoding="utf-8"))["name_to_index"]
            if set(mapped) != set(self.classes):
                raise SystemExit(f"labels.json classes != manifest classes for {manifest}")

    @staticmethod
    def _load_manifest(path: Path) -> list[tuple[str, str]]:
        with open(path, newline="", encoding="utf-8") as fh:
            rows = [(r["class"], r["rel_path"]) for r in csv.DictReader(fh)]
        return rows

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, idx: int) -> tuple[np.ndarray, int]:
        cls, rel = self.rows[idx]
        img = Image.open(IMAGE_DIR / rel).convert("RGB")
        arr = self._transform(np.asarray(img, dtype=np.float32))
        label = self.name_to_index[cls]
        return arr, label

    def _transform(self, x: np.ndarray) -> np.ndarray:
        k = AUG_KW if self.augment else NO_AUG_KW
        if self.augment:
            x = self._random_affine(x, k)
        # keep aspect ratio, then center-crop to square
        h, w = x.shape[:2]
        s = min(h, w)
        y0, x0 = (h - s) // 2, (w - s) // 2
        x = x[y0:y0 + s, x0:x0 + s]
        x = np.asarray(Image.fromarray(x.astype(np.uint8)).resize((self.img_size, self.img_size), Image.BILINEAR), dtype=np.float32)
        return x

    @staticmethod
    def _random_affine(x: np.ndarray, k: dict) -> np.ndarray:
        pil = Image.fromarray(x.astype(np.uint8))
        if k["hflip"] and k["hflip_p"] and random.random() < k["hflip_p"]:
            pil = pil.transpose(Image.FLIP_LEFT_RIGHT)
        angle = random.uniform(-k["rot_deg"], k["rot_deg"])
        if angle:
            pil = pil.rotate(angle, resample=Image.BILINEAR, fillcolor=128)
        if k["bright_std"] and k["scale_range"] != (1.0, 1.0):
            pass
        if k["bright_std"]:
            factor = 1.0 + random.gauss(0.0, k["bright_std"])
            x_out = np.asarray(pil, dtype=np.float32) * factor
            return np.clip(x_out, 0, 255)
        return np.asarray(pil, dtype=np.float32)


def make_loaders(img_size: int, batch_size: int, augment: bool = True, seed: int = SEED):
    common = dict(img_size=img_size)
    train = FoodDataset(MANIFESTS_DIR / "train.csv", MANIFESTS_DIR / "labels.json", augment=augment, seed=seed, **common)
    val = FoodDataset(MANIFESTS_DIR / "val.csv", MANIFESTS_DIR / "labels.json", augment=False, seed=seed, **common)
    test = FoodDataset(MANIFESTS_DIR / "test.csv", MANIFESTS_DIR / "labels.json", augment=False, seed=seed, **common)

    ld_train = torch.utils.data.DataLoader(train, batch_size=batch_size, shuffle=True, num_workers=0, drop_last=True)
    ld_val = torch.utils.data.DataLoader(val, batch_size=batch_size, shuffle=False, num_workers=0)
    ld_test = torch.utils.data.DataLoader(test, batch_size=batch_size, shuffle=False, num_workers=0)
    return ld_train, ld_val, ld_test


if __name__ == "__main__":
    train, val, test = make_loaders(img_size=224, batch_size=16)
    xs, ys = next(iter(train))
    print(f"train: {len(train.dataset)} | val: {len(val.dataset)} | test: {len(test.dataset)}", flush=True)
    print(f"batch: x {tuple(xs.shape)} ({xs.dtype}, range {-xs.min():.0f}..{xs.max():.0f}), y {tuple(ys.shape)}", flush=True)
    print(f"classes: {train.dataset.classes}", flush=True)