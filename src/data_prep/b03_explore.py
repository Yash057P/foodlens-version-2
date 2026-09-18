"""Batch 3 - Explore the subset.

Builds a 20-class contact sheet (one image per class) and a per-class train/val
image-count bar chart into results/figures/.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

from config import FIGURES_DIR, IMAGE_DIR, MANIFESTS_DIR, SUBSET_CLASSES

plt.rcParams.update({"font.size": 8})


def contact_sheet() -> None:
    per_class = {}
    for line in (MANIFESTS_DIR / "train.csv").read_text(encoding="utf-8").splitlines()[1:]:
        cls, rel = line.split(",")
        per_class.setdefault(cls, []).append(rel)
    fig, axes = plt.subplots(4, 5, figsize=(12, 10))
    for ax, cls in enumerate(sorted(SUBSET_CLASSES)):
        img = Image.open(IMAGE_DIR / per_class[cls][0]).convert("RGB")
        r, c = divmod(ax, 5)
        axes[r, c].imshow(img)
        axes[r, c].set_title(cls.replace("_", "\n"), fontsize=9)
        axes[r, c].axis("off")
    fig.suptitle("Food-101 subset - one sample per class", fontsize=13)
    out = FIGURES_DIR / "gallery_20classes.png"
    fig.tight_layout()
    fig.savefig(out, dpi=110)
    plt.close(fig)
    print("gallery ->", out, flush=True)


def class_counts() -> None:
    from collections import Counter
    counts = Counter()
    for line in (MANIFESTS_DIR / "train.csv").read_text(encoding="utf-8").splitlines()[1:]:
        counts[line.split(",")[0]] += 1
    names = sorted(counts)
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.bar(names, [counts[n] for n in names])
    ax.set_ylabel("train images / class")
    ax.set_xticklabels([n.replace("_", " ") for n in names], rotation=60, ha="right")
    out = FIGURES_DIR / "class_counts.png"
    fig.tight_layout()
    fig.savefig(out, dpi=110)
    plt.close(fig)
    print("class counts ->", out, flush=True)


if __name__ == "__main__":
    contact_sheet()
    class_counts()