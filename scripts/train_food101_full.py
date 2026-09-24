#!/usr/bin/env python3
"""Train EfficientNetV2S on all 101 Food-101 classes.

The official train split is divided deterministically into 90% train and 10%
validation per class. The official test split remains untouched until the final
evaluation. Images are decoded on demand so the full dataset is not loaded into
RAM. The saved model accepts raw RGB pixels in [0, 255], matching webapp/inference.py.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import time
from pathlib import Path

os.environ.setdefault("KERAS_BACKEND", "tensorflow")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import numpy as np
import tensorflow as tf
import keras

ROOT = Path(__file__).resolve().parents[1]
FOOD101_DIR = ROOT / "data" / "extracted" / "food-101"
RESULTS_DIR = ROOT / "results"
DEFAULT_OUTPUT = RESULTS_DIR / "food101_efficientnetv2s.keras"
SEED = 42
IMG_SIZE = 224


def read_rows(filename: str) -> list[tuple[str, int]]:
    classes = sorted(
        line.strip().split("/")[0]
        for line in (FOOD101_DIR / "meta" / "train.txt").read_text(encoding="utf-8").splitlines()
        if line.strip()
    )
    class_to_index = {name: index for index, name in enumerate(classes)}
    rows = []
    for line in (FOOD101_DIR / "meta" / filename).read_text(encoding="utf-8").splitlines():
        rel = line.strip()
        if rel:
            rows.append((rel, class_to_index[rel.split("/")[0]]))
    return rows, classes


def make_train_val_rows(val_fraction: float) -> tuple[list[tuple[str, int]], list[tuple[str, int]], list[str]]:
    all_rows, classes = read_rows("train.txt")
    by_class: dict[int, list[tuple[str, int]]] = {i: [] for i in range(len(classes))}
    for row in all_rows:
        by_class[row[1]].append(row)
    rng = random.Random(SEED)
    train_rows, val_rows = [], []
    for label in range(len(classes)):
        rows = by_class[label]
        rng.shuffle(rows)
        n_val = max(1, int(round(len(rows) * val_fraction)))
        val_rows.extend(rows[:n_val])
        train_rows.extend(rows[n_val:])
    return train_rows, val_rows, classes


def path_for(rel: str) -> str:
    return str(FOOD101_DIR / "images" / f"{rel}.jpg")


def decode_image(path: tf.Tensor, label: tf.Tensor) -> tuple[tf.Tensor, tf.Tensor]:
    image = tf.io.read_file(path)
    image = tf.image.decode_jpeg(image, channels=3)
    image = tf.image.resize(image, [IMG_SIZE, IMG_SIZE], method="bilinear")
    return tf.cast(image, tf.float32), label


def make_dataset(rows: list[tuple[str, int]], batch_size: int, training: bool) -> tf.data.Dataset:
    paths = np.asarray([path_for(rel) for rel, _ in rows], dtype=str)
    labels = np.asarray([label for _, label in rows], dtype=np.int32)
    dataset = tf.data.Dataset.from_tensor_slices((paths, labels))
    if training:
        dataset = dataset.shuffle(min(len(rows), 10000), seed=SEED, reshuffle_each_iteration=True)
    dataset = dataset.map(decode_image, num_parallel_calls=tf.data.AUTOTUNE)
    return dataset.batch(batch_size).prefetch(tf.data.AUTOTUNE)


def build_model(num_classes: int, learning_rate: float) -> tuple[keras.Model, keras.Model]:
    base = keras.applications.EfficientNetV2S(
        include_top=False,
        weights="imagenet",
        input_shape=(IMG_SIZE, IMG_SIZE, 3),
        pooling=None,
    )
    base.trainable = False
    inputs = keras.Input((IMG_SIZE, IMG_SIZE, 3), name="image")
    augmented = keras.Sequential(
        [
            keras.layers.RandomFlip("horizontal"),
            keras.layers.RandomRotation(0.08),
            keras.layers.RandomZoom(0.10),
            keras.layers.RandomContrast(0.10),
        ],
        name="food_augmentation",
    )(inputs)
    x = base(augmented, training=False)
    x = keras.layers.GlobalAveragePooling2D()(x)
    x = keras.layers.BatchNormalization()(x)
    x = keras.layers.Dense(1024, activation="relu", kernel_regularizer=keras.regularizers.l2(1e-4))(x)
    x = keras.layers.Dropout(0.35)(x)
    x = keras.layers.Dense(512, activation="relu", kernel_regularizer=keras.regularizers.l2(1e-4))(x)
    x = keras.layers.Dropout(0.25)(x)
    outputs = keras.layers.Dense(num_classes, activation="softmax")(x)
    model = keras.Model(inputs, outputs, name="Food101_EfficientNetV2S")
    model.compile(
        optimizer=keras.optimizers.AdamW(learning_rate=learning_rate, weight_decay=1e-4),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model, base


def evaluate(model: keras.Model, dataset: tf.data.Dataset, labels: np.ndarray) -> dict[str, float]:
    probabilities = model.predict(dataset, verbose=1)
    order = np.argsort(probabilities, axis=1)
    metrics = {}
    for k in (1, 3, 5):
        metrics[f"top{k}"] = float(np.mean([labels[i] in order[i, -k:] for i in range(len(labels))]))
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs-frozen", type=int, default=8)
    parser.add_argument("--epochs-finetune", type=int, default=12)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--val-fraction", type=float, default=0.10)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    tf.random.set_seed(SEED)
    np.random.seed(SEED)
    train_rows, val_rows, classes = make_train_val_rows(args.val_fraction)
    test_rows, _ = read_rows("test.txt")
    print(f"classes={len(classes)} train={len(train_rows)} val={len(val_rows)} test={len(test_rows)}", flush=True)

    train_ds = make_dataset(train_rows, args.batch_size, training=True)
    val_ds = make_dataset(val_rows, args.batch_size, training=False)
    test_ds = make_dataset(test_rows, args.batch_size, training=False)
    val_labels = np.asarray([label for _, label in val_rows], dtype=np.int32)
    test_labels = np.asarray([label for _, label in test_rows], dtype=np.int32)

    model, base = build_model(len(classes), learning_rate=1e-3)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    callbacks = [
        keras.callbacks.ModelCheckpoint(args.output, monitor="val_accuracy", mode="max", save_best_only=True, verbose=1),
        keras.callbacks.EarlyStopping(monitor="val_accuracy", mode="max", patience=3, restore_best_weights=True),
        keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.2, patience=2, min_lr=1e-6),
    ]

    started = time.time()
    print("Phase 1: frozen ImageNet backbone", flush=True)
    model.fit(train_ds, validation_data=val_ds, epochs=args.epochs_frozen, callbacks=callbacks, verbose=1)

    base.trainable = True
    for layer in base.layers[:-30]:
        layer.trainable = False
    model.compile(
        optimizer=keras.optimizers.AdamW(learning_rate=1e-5, weight_decay=1e-4),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    print("Phase 2: fine-tuning final backbone blocks", flush=True)
    model.fit(train_ds, validation_data=val_ds, epochs=args.epochs_finetune, callbacks=callbacks, verbose=1)

    model.save(args.output)
    val_metrics = evaluate(model, val_ds, val_labels)
    test_metrics = evaluate(model, test_ds, test_labels)
    metrics = {
        "dataset": "Food-101",
        "classes": len(classes),
        "train_images": len(train_rows),
        "validation_images": len(val_rows),
        "test_images": len(test_rows),
        "val": val_metrics,
        "test": test_metrics,
        "elapsed_seconds": round(time.time() - started, 1),
        "model": str(args.output),
    }
    metrics_path = args.output.with_suffix(".metrics.json")
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (args.output.with_suffix(".classes.json")).write_text(
        json.dumps({"index_to_name": {str(i): name for i, name in enumerate(classes)}}, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(metrics, indent=2), flush=True)


if __name__ == "__main__":
    main()
