"""Evaluate the trained best_model.keras on the official Food-101 test split.

Replicates the training notebook's preprocessing: JPEG decode -> resize to
(224,224) bilinear (squash, as tf.image.resize does) -> float32, no extra
normalization. Reports top-1, top-5, per-class accuracy, worst classes, and
measured inference throughput.
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
from PIL import Image
from sklearn.metrics import accuracy_score

from config import FOOD101_DIR

IMG_SIZE = 224
BATCH = 64
MODEL_PATH = Path("best_model.keras")


def build_class_map() -> dict[str, int]:
    names = set()
    for line in (FOOD101_DIR / "meta" / "train.txt").read_text(encoding="utf-8").splitlines():
        if line.strip():
            names.add(line.strip().split("/")[0])
    return {name: i for i, name in enumerate(sorted(names))}


def load_test():
    class_map = build_class_map()
    rows = []
    for line in (FOOD101_DIR / "meta" / "test.txt").read_text(encoding="utf-8").splitlines():
        rel = line.strip()
        if not rel:
            continue
        rows.append((rel, class_map[rel.split("/")[0]]))
    return rows, class_map


def decode(path: Path) -> np.ndarray:
    img = Image.open(path).convert("RGB").resize((IMG_SIZE, IMG_SIZE), Image.BILINEAR)
    return np.asarray(img, dtype=np.uint8)


def main() -> None:
    print("loading model...", flush=True)
    import keras
    model = keras.models.load_model(str(MODEL_PATH), compile=False)
    print("model loaded", flush=True)

    rows, class_map = load_test()
    idx_to_name = {i: n for n, i in class_map.items()}
    print(f"test images: {len(rows)} | classes: {len(class_map)}", flush=True)

    # build uint8 array in batches (memory-friendly), cached on disk
    import numpy as np
    cache_path = Path("data/preprocessed/full_test_cache.npz")
    if cache_path.exists():
        data = np.load(cache_path)
        X, Y = data["X"], data["Y"]
        print(f"cache hit ({X.shape[0]} imgs)", flush=True)
    else:
        X = np.empty((len(rows), IMG_SIZE, IMG_SIZE, 3), dtype=np.uint8)
        Y = np.empty((len(rows),), dtype=int)
        for i, (rel, label) in enumerate(rows):
            X[i] = decode(FOOD101_DIR / "images" / f"{rel}.jpg")
            Y[i] = label
            if i and i % 4000 == 0:
                print(f"  decoded {i}/{len(rows)}", flush=True)
        np.savez_compressed(cache_path, X=X, Y=Y)
        print(f"  decoded all {len(rows)} (cached)", flush=True)

    # evaluate on GPU
    t0 = time.time()
    preds = []
    for start in range(0, len(rows), BATCH):
        xb = X[start:start + BATCH].astype(np.float32)
        out = model(np.asarray(xb))
        prob = keras.ops.convert_to_numpy(out)
        preds.append(prob)
    prob_all = np.concatenate(preds)
    dt = time.time() - t0
    y_pred = prob_all.argmax(1)
    yp5 = np.argsort(prob_all, axis=1)[:, -5:]

    acc1 = accuracy_score(Y, y_pred)
    yp3 = np.argsort(prob_all, axis=1)[:, -3:]
    yp5 = np.argsort(prob_all, axis=1)[:, -5:]
    top3 = np.mean([Y[i] in yp3[i] for i in range(len(Y))])
    top5 = np.mean([Y[i] in yp5[i] for i in range(len(Y))])
    print(f"\nTop-1 accuracy: {acc1:.4f}")
    print(f"Top-3 accuracy: {top3:.4f}")
    print(f"Top-5 accuracy: {top5:.4f}")
    print(f"GPU eval time: {dt:.1f}s for {len(rows)} imgs -> {1000*dt/len(rows):.2f} ms/img (batch {BATCH})")

    Path("data/preprocessed/food101_preds.npz").parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed("data/preprocessed/food101_preds.npz", Y=Y, probs=prob_all)
    print("predictions cached -> data/preprocessed/food101_preds.npz")

    # per-class accuracy
    from collections import defaultdict
    cls_correct = defaultdict(int)
    cls_total = defaultdict(int)
    for i in range(len(Y)):
        cls_total[Y[i]] += 1
        cls_correct[Y[i]] += int(y_pred[i] == Y[i])
    per_class = {idx_to_name[c]: cls_correct[c] / cls_total[c] for c in cls_total}
    worst = sorted(per_class.items(), key=lambda kv: kv[1])[:10]
    best = sorted(per_class.items(), key=lambda kv: kv[1])[-5:][::-1]
    print("\nWorst 10 classes:")
    for n, a in worst:
        print(f"  {n:24s} {a:.2f}")
    print("\nBest 5 classes:")
    for n, a in best:
        print(f"  {n:24s} {a:.2f}")

    out = {
        "top1": float(acc1),
        "top3": float(top3),
        "top5": float(top5),
        "ms_per_image_batched": float(1000 * dt / len(rows)),
        "test_size": len(rows),
        "model_mb": round(Path(MODEL_PATH).stat().st_size / 1e6, 2),
        "worst_classes": [[n, round(a, 3)] for n, a in worst],
    }
    Path("results/food101_eval.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("\n-> results/food101_eval.json")


if __name__ == "__main__":
    main()