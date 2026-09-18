"""Batch 6 - Stratified fixed splits.

From the official 750 train images per class: deterministic shuffle (seed fixed)
then take 600 per class into train split and 150 per class into val split.
Test split = the official 250 test images, stored separately but NOT used by any
Module 2 code path (Batch 37 unlocks it).

Emits manifests/train.csv, val.csv, test.csv of the form class,rel_path.
"""
import csv
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from config import MANIFESTS_DIR, SUBSET_CLASSES, TRAIN_META, TEST_META, SEED, TRAIN_PER_CLASS, VAL_PER_CLASS


def read_train_files() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for line in TRAIN_META.read_text(encoding="utf-8").splitlines():
        rel = line.strip()
        if not rel:
            continue
        cls, _ = rel.split("/")
        if cls in SUBSET_CLASSES:
            out.setdefault(cls, []).append(rel + ".jpg")
    return out


def read_test_files() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for line in TEST_META.read_text(encoding="utf-8").splitlines():
        rel = line.strip()
        if not rel:
            continue
        cls, _ = rel.split("/")
        if cls in SUBSET_CLASSES:
            out.setdefault(cls, []).append(rel + ".jpg")
    return out


def main() -> None:
    rng = random.Random(SEED)
    train_files = read_train_files()
    test_files = read_test_files()

    train_rows, val_rows, test_rows = [], [], []
    for cls in SUBSET_CLASSES:
        files = train_files.get(cls) or []
        rng.shuffle(files)
        if len(files) < TRAIN_PER_CLASS + VAL_PER_CLASS:
            raise SystemExit(f"class {cls}: only {len(files)} train images")
        train_rows += [(cls, rel) for rel in files[:TRAIN_PER_CLASS]]
        val_rows += [(cls, rel) for rel in files[TRAIN_PER_CLASS: TRAIN_PER_CLASS + VAL_PER_CLASS]]
        test_rows += [(cls, rel) for rel in test_files.get(cls) or []]

    for name, rows in (("train", train_rows), ("val", val_rows), ("test", test_rows)):
        path = MANIFESTS_DIR / f"{name}.csv"
        with open(path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["class", "rel_path"])
            writer.writerows(rows)
        print(f"{name}: {len(rows)} rows -> {path}", flush=True)

    # per-class sanity counts
    from collections import Counter
    for name, rows in (("train", train_rows), ("val", val_rows), ("test", test_rows)):
        counts = Counter(cls for cls, _ in rows)
        if len(counts) != len(SUBSET_CLASSES):
            raise SystemExit(f"split {name} missing classes!")


if __name__ == "__main__":
    main()