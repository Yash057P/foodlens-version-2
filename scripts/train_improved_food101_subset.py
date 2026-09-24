#!/usr/bin/env python3
"""Train a stronger EfficientNetV2S model on the project Food-101 subset.

This script is designed for the current CPU-only dev environment: it uses the
cached uint8 arrays created by src/data_prep/data_cache.py and processes them via
TensorFlow tf.data to keep memory use manageable while still training a realistic
transfer-learning model.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

os.environ.setdefault("KERAS_BACKEND", "tensorflow")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import numpy as np
import tensorflow as tf
import keras

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def build_model(num_classes: int = 20) -> keras.Model:
    base = keras.applications.EfficientNetV2S(
        include_top=False,
        weights="imagenet",
        input_shape=(224, 224, 3),
    )
    base.trainable = False
    inputs = keras.Input(shape=(224, 224, 3), name="image")
    x = keras.layers.Rescaling(scale=1.0 / 255.0)(inputs)
    x = base(x, training=False)
    x = keras.layers.GlobalAveragePooling2D()(x)
    x = keras.layers.BatchNormalization()(x)
    x = keras.layers.Dense(1024, activation="relu", kernel_regularizer=keras.regularizers.l2(1e-4))(x)
    x = keras.layers.Dropout(0.35)(x)
    x = keras.layers.Dense(512, activation="relu", kernel_regularizer=keras.regularizers.l2(1e-4))(x)
    x = keras.layers.Dropout(0.25)(x)
    outputs = keras.layers.Dense(num_classes, activation="softmax")(x)
    model = keras.Model(inputs, outputs, name="Food101_EfficientNetV2S_Subset")
    return model


def make_dataset(x: np.ndarray, y: np.ndarray, train: bool = False, batch_size: int = 32):
    ds = tf.data.Dataset.from_tensor_slices((x, y))
    if train:
        ds = ds.shuffle(buffer_size=min(len(y), 4096))
    ds = ds.batch(batch_size)
    ds = ds.map(lambda xb, yb: (tf.cast(xb, tf.float32) / 255.0, tf.cast(yb, tf.int32)), num_parallel_calls=tf.data.AUTOTUNE)
    ds = ds.prefetch(tf.data.AUTOTUNE)
    return ds


def topk_accuracy(prob: np.ndarray, y_true: np.ndarray, k: int) -> float:
    idx = np.argsort(prob, axis=1)[:, -k:]
    return float(np.mean([y_true[i] in idx[i] for i in range(len(y_true))]))


def main() -> None:
    train_x = np.load(ROOT / "data" / "preprocessed" / "train_x.npy")
    train_y = np.load(ROOT / "data" / "preprocessed" / "train_y.npy").astype(np.int32)
    val_x = np.load(ROOT / "data" / "preprocessed" / "val_x.npy")
    val_y = np.load(ROOT / "data" / "preprocessed" / "val_y.npy").astype(np.int32)
    test_x = np.load(ROOT / "data" / "preprocessed" / "test_x.npy")
    test_y = np.load(ROOT / "data" / "preprocessed" / "test_y.npy").astype(np.int32)

    train_ds = make_dataset(train_x, train_y, train=True, batch_size=32)
    val_ds = make_dataset(val_x, val_y, train=False, batch_size=64)

    model = build_model(num_classes=20)
    model.compile(
        optimizer=keras.optimizers.AdamW(learning_rate=1e-3, weight_decay=1e-4),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )

    print("\nPhase 1: train classification head")
    t0 = time.time()
    hist1 = model.fit(train_ds, validation_data=val_ds, epochs=2, verbose=1)
    phase1_time = time.time() - t0

    base = model.layers[1] if len(model.layers) > 1 else None
    if base is not None and hasattr(base, "layers"):
        base.trainable = True
        for layer in base.layers[:-25]:
            layer.trainable = False

    model.compile(
        optimizer=keras.optimizers.AdamW(learning_rate=1e-5, weight_decay=1e-4),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )

    print("\nPhase 2: fine-tune final EfficientNetV2S blocks")
    t1 = time.time()
    hist2 = model.fit(train_ds, validation_data=val_ds, epochs=2, verbose=1)
    phase2_time = time.time() - t1

    val_pred = model.predict(val_x / 255.0, batch_size=64, verbose=0)
    test_pred = model.predict(test_x / 255.0, batch_size=64, verbose=0)
    val_top1 = float(np.mean(np.argmax(val_pred, axis=1) == val_y))
    val_top3 = topk_accuracy(val_pred, val_y, 3)
    test_top1 = float(np.mean(np.argmax(test_pred, axis=1) == test_y))
    test_top3 = topk_accuracy(test_pred, test_y, 3)

    model_path = RESULTS_DIR / "food101_improved_subset.keras"
    model.save(model_path)

    metrics = {
        "dataset": "Food-101 subset (20 classes)",
        "phase1_epochs": len(hist1.history["loss"]),
        "phase2_epochs": len(hist2.history["loss"]),
        "phase1_seconds": round(phase1_time, 2),
        "phase2_seconds": round(phase2_time, 2),
        "val_top1": val_top1,
        "val_top3": val_top3,
        "test_top1": test_top1,
        "test_top3": test_top3,
        "model_path": str(model_path),
    }
    metrics_path = RESULTS_DIR / "food101_improved_subset_metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print("\nRESULTS")
    print(json.dumps(metrics, indent=2))
    print(f"\nSaved model -> {model_path}")
    print(f"Saved metrics -> {metrics_path}")


if __name__ == "__main__":
    main()
