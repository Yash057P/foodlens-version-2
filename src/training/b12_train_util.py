"""Batch 12 - Training utilities.

A Keras-native `PreprocessSequence` (keras.utils.Sequence) that holds the
uint8 numpy cache in memory and, per batch, decodes to float32 and applies the
given preprocess_fn. This is a first-class Keras data adapter, so model.fit
works on both torch and tf backends without extra plumbing.
"""
import csv
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import keras
import numpy as np

from config import FIGURES_DIR, RESULTS_DIR, SEED

TRAIN_DIR = RESULTS_DIR / "training"
TRAIN_DIR.mkdir(parents=True, exist_ok=True)


class PreprocessSequence(keras.utils.Sequence):
    def __init__(self, x, y, preprocess_fn, batch_size: int = 32, shuffle: bool = True, seed: int = SEED):
        self.x = x
        self.y = y
        self.preprocess_fn = preprocess_fn
        self.batch_size = batch_size
        self.shuffle = shuffle
        self.n = len(x)
        self.indices = np.arange(self.n)
        self.rng = random.Random(seed)

    def __len__(self) -> int:
        return int(np.ceil(self.n / self.batch_size))

    def __getitem__(self, i: int):
        idx = self.indices[i * self.batch_size: (i + 1) * self.batch_size]
        xb = self.x[idx].astype(np.float32)
        xb = self.preprocess_fn(np.ascontiguousarray(xb))
        return xb, self.y[idx]

    def on_epoch_end(self) -> None:
        if self.shuffle:
            self.rng.shuffle(self.indices)


def _save_history(history: keras.callbacks.History, name: str, stage: str) -> Path:
    path = TRAIN_DIR / f"{name}_{stage}_history.csv"
    keys = list(history.history.keys())
    with open(path, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["epoch"] + keys)
        for i in range(len(history.history[keys[0]])):
            writer.writerow([i + 1] + [f"{history.history[k][i]:.6f}" for k in keys])
    return path


def _plot_history(history: keras.callbacks.History, name: str, stage: str) -> Path:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    acc = [k for k in history.history if "acc" in k]
    if acc:
        axes[0].plot(history.history[acc[0]], label=acc[0])
        val_acc = [k for k in history.history if "val_acc" in k]
        if val_acc:
            axes[0].plot(history.history[val_acc[0]], label=val_acc[0])
        axes[0].legend()
        axes[0].set_title(f"{name} {stage} accuracy")
    loss = [k for k in history.history if k == "loss" or (k == "loss")]
    if loss:
        axes[1].plot(history.history[loss[0]], label="loss")
        val_loss = [k for k in history.history if "val_loss" in k]
        if val_loss:
            axes[1].plot(history.history[val_loss[0]], label="val_loss")
        axes[1].legend()
        axes[1].set_title(f"{name} {stage} loss")
    path = FIGURES_DIR / f"{name}_{stage}_training.png"
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path


def train_stage(
    model: keras.Model,
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_val: np.ndarray,
    y_val: np.ndarray,
    preprocess_fn,
    epochs: int,
    lr: float,
    name: str,
    stage: str,
    patience: int = 3,
    finetune_from: int | None = None,
    batch_size: int = 32,
) -> keras.callbacks.History:
    if finetune_from is not None:
        model.trainable = True
        for layer in model.layers[:finetune_from]:
            layer.trainable = False
        print(f"  {name}: fine-tuning from layer {finetune_from} / {len(model.layers)}", flush=True)

    model.compile(optimizer=keras.optimizers.Adam(lr), loss="sparse_categorical_crossentropy", metrics=["accuracy"])

    train_seq = PreprocessSequence(x_train, y_train, preprocess_fn, batch_size=batch_size, shuffle=True)
    val_seq = PreprocessSequence(x_val, y_val, preprocess_fn, batch_size=batch_size, shuffle=False)

    callbacks = [
        keras.callbacks.EarlyStopping(monitor="val_accuracy", patience=patience, restore_best_weights=True),
        keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.2, patience=max(1, patience - 1), min_lr=1e-7),
    ]

    history = model.fit(train_seq, validation_data=val_seq, epochs=epochs, callbacks=callbacks, verbose=1)

    _save_history(history, name, stage)
    _plot_history(history, name, stage)
    print(f"  {name}/{stage} finished (epochs={len(history.history['loss'])})", flush=True)
    return history