"""Benchmark architecture cost only; this script intentionally makes no accuracy claims."""
import argparse
import json
import time
from pathlib import Path

import numpy as np
import tensorflow as tf


def custom_cnn():
    inputs = tf.keras.Input((224, 224, 3))
    x = inputs
    for filters in (32, 64, 128):
        x = tf.keras.layers.Conv2D(filters, 3, padding="same", activation="relu")(x)
        x = tf.keras.layers.MaxPool2D()(x)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    return tf.keras.Model(inputs, tf.keras.layers.Dense(101, activation="softmax")(x), name="CustomCNN")


def build_models():
    return [
        custom_cnn(),
        tf.keras.applications.MobileNetV2(input_shape=(224, 224, 3), weights=None, classes=101),
        tf.keras.applications.EfficientNetB0(input_shape=(224, 224, 3), weights=None, classes=101),
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="artifacts/architecture_cost_benchmark.json")
    parser.add_argument("--runs", type=int, default=5)
    args = parser.parse_args()
    batch = np.zeros((1, 224, 224, 3), dtype=np.float32)
    results = []
    for model in build_models():
        model(batch, training=False)
        samples = []
        for _ in range(args.runs):
            started = time.perf_counter()
            model(batch, training=False)
            samples.append((time.perf_counter() - started) * 1000)
        results.append({
            "architecture": model.name,
            "parameters": int(model.count_params()),
            "estimated_fp32_weights_mib": round(model.count_params() * 4 / 1024 / 1024, 2),
            "median_latency_ms": round(float(np.median(samples)), 2),
        })
    report = {
        "scope": "engineering_cost_only",
        "warning": "Models use random weights. No accuracy or quality comparison is implied.",
        "device": tf.config.list_physical_devices()[0].device_type if tf.config.list_physical_devices() else "unknown",
        "runs": args.runs,
        "results": results,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
