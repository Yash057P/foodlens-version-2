"""Batch 13 - Smoke test the full training pipeline end to end.

Runs a single frozen-head epoch over a 16-batch slice for all 5 models, saving
history CSV + figure and verifying the saved .keras model reloads.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import keras
import numpy as np

from config import BATCH_SIZE, MODELS_DIR, RESULTS_DIR, SEED
from src.data_prep.data_cache import build_cache, load_cache
from src.training.b11_build import MODEL_BUILDERS
from src.training.b12_train_util import train_stage

SMOKE_STEPS = 16
SMOKE_EPOCHS = 1

PREPROCESS = {
    "CustomCNN": lambda x: x,
    "ResNet50": keras.applications.resnet50.preprocess_input,
    "MobileNetV2": keras.applications.mobilenet_v2.preprocess_input,
    "DenseNet121": keras.applications.densenet.preprocess_input,
    "EfficientNetB0": keras.applications.efficientnet.preprocess_input,
}


def main() -> None:
    build_cache()
    x_train, y_train = load_cache("train")
    x_val, y_val = load_cache("val")

    results = []
    for name, builder in MODEL_BUILDERS.items():
        t0 = time.time()
        model = builder(num_classes=20)
        print(f"\n{'='*60}\nSMOKE {name} ({model.count_params():,} params)\n{'='*60}", flush=True)

        # deliberate overshoot: smoke uses a full val seq but its own 16-step train slice
        train_slice = int(SMOKE_STEPS * BATCH_SIZE)
        train_stage(
            model,
            x_train[:train_slice],
            y_train[:train_slice],
            x_val,
            y_val,
            PREPROCESS[name],
            epochs=SMOKE_EPOCHS,
            lr=1e-3,
            name=name,
            stage="smoke",
            patience=1,
            batch_size=BATCH_SIZE,
        )
        elapsed = time.time() - t0

        path = MODELS_DIR / f"{name}_smoke.keras"
        model.save(str(path))
        loaded = keras.models.load_model(str(path))
        out = loaded(PREPROCESS[name](np.random.rand(1, 224, 224, 3).astype("float32")))
        ok = out.shape == (1, 20) and abs(float(keras.ops.convert_to_numpy(out).sum()) - 1.0) < 0.05
        results.append((name, model.count_params(), elapsed, ok))
        print(f"  {name} smoke OK: {elapsed:.1f}s load={ok}", flush=True)
        del model, loaded

    print("\nSMOKE SUMMARY")
    for name, params, elapsed, ok in results:
        print(f"{name:<16} {params:>12,} {elapsed:5.1f}s {str(ok):>4}")
    out = RESULTS_DIR / "smoke_log.txt"
    out.write_text("model,params,elapsed_s,ok\n" + "\n".join(f"{n},{p},{e:.1f},{o}" for n, p, e, o in results) + "\n", encoding="utf-8")
    print("log ->", out, flush=True)


if __name__ == "__main__":
    main()