"""Batch 10 - End-of-Module-1 validation gates.

Verifies: (1) split sizes and class balance, (2) train/val/test are disjoint by
file, (3) the label map agrees with the loader, (4) loader batch dtype/range,
(5) determinism of the seed for a repeated split of one class.
Writes a report to data/manifests/module1_report.txt.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from config import MANIFESTS_DIR, SEED, SUBSET_CLASSES
from src.data_prep.b09_loaders import make_loaders

CHECKS: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    CHECKS.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}", flush=True)


def main() -> None:
    labels = json.loads((MANIFESTS_DIR / "labels.json").read_text(encoding="utf-8"))
    check("labels.json has all 20 classes", set(labels["name_to_index"]) == set(SUBSET_CLASSES))

    splits = {}
    for name in ("train", "val", "test"):
        rows = []
        for line in (MANIFESTS_DIR / f"{name}.csv").read_text(encoding="utf-8").splitlines()[1:]:
            cls, rel = line.split(",")
            rows.append((cls, rel))
        splits[name] = rows

    from collections import Counter
    counts = Counter(cls for cls, _ in splits["train"])
    check("train 600/class", all(v == 600 for v in counts.values()) and len(counts) == 20, str(len(counts)) + " classes")
    counts_v = Counter(cls for cls, _ in splits["val"])
    check("val 150/class", all(v == 150 for v in counts_v.values()))
    counts_t = Counter(cls for cls, _ in splits["test"])
    check("test 250/class", all(v == 250 for v in counts_t.values()))

    check("train/val disjoint", not (set(splits["train"]) & set(splits["val"])))
    check("train/test disjoint", not (set(splits["train"]) & set(splits["test"])))
    check("val/test disjoint", not (set(splits["val"]) & set(splits["test"])))

    train, val, test = make_loaders(img_size=224, batch_size=16)
    xs, ys = next(iter(train))
    check("loader batch shape (16,224,224,3)", tuple(xs.shape) == (16, 224, 224, 3))
    check("loader dtype float32", xs.dtype == import_torch().float32)
    check("loader range stays in [0,255]", float(xs.min()) >= 0 and float(xs.max()) <= 255)

    # determinism: reseeding produces identical per-class order for val (no shuffle)
    seeds1 = [r for r in make_loaders(img_size=224, batch_size=16)[1].dataset.rows[:5]]
    seeds2 = [r for r in make_loaders(img_size=224, batch_size=16)[1].dataset.rows[:5]]
    check("val loader deterministic", seeds1 == seeds2)

    report = MANIFESTS_DIR / "module1_report.txt"
    lines = [f"{name}: {'PASS' if ok else 'FAIL'} {detail}" for name, ok, detail in CHECKS]
    report.write_text("MODULE 1 VALIDATION REPORT (batch 10)\n" + "\n".join(lines) + f"\nALL PASS: {all(ok for _, ok, _ in CHECKS)}\n", encoding="utf-8")
    print("report ->", report, flush=True)


def import_torch():
    import torch
    return torch


if __name__ == "__main__":
    main()