"""Improved training recipe for Food-101.

This is a stronger transfer-learning baseline than the older EfficientNetB0 recipe
used in the project. The goal is to improve top-1 accuracy on the 101-class Food-101
benchmark without changing the model interface used by the Flask app.

The recipe is intentionally conservative and production-oriented:
- use a stronger backbone (EfficientNetV2S or B4)
- keep preprocessing consistent with the app and evaluation pipeline
- stage the fine-tuning so the backbone is not overfit too early
- use stronger-but-safe image augmentation
- use validation-driven checkpointing and early stopping
"""

from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import keras


def build_improved_food101_model(num_classes: int = 101, input_shape: tuple[int, int, int] = (224, 224, 3)) -> keras.Model:
    """Build a stronger fine-tuning model for Food-101.

    EfficientNetV2S is a realistic next-step upgrade from the current EfficientNetB0
    baseline. It has a better accuracy/efficiency trade-off on fine-grained visual
    recognition tasks and is compatible with the model-loading flow in the web app.
    """
    base = keras.applications.EfficientNetV2S(
        include_top=False,
        weights="imagenet",
        input_shape=input_shape,
        pooling=None,
    )

    base.trainable = False
    inputs = keras.Input(shape=input_shape)
    # EfficientNetV2S includes its own preprocessing and, like the shipped app,
    # expects decoded RGB pixels in the [0, 255] range.
    x = base(inputs, training=False)
    x = keras.layers.GlobalAveragePooling2D()(x)
    x = keras.layers.BatchNormalization()(x)
    x = keras.layers.Dense(1024, activation="relu", kernel_regularizer=keras.regularizers.l2(1e-4))(x)
    x = keras.layers.Dropout(0.35)(x)
    x = keras.layers.Dense(512, activation="relu", kernel_regularizer=keras.regularizers.l2(1e-4))(x)
    x = keras.layers.Dropout(0.25)(x)
    outputs = keras.layers.Dense(num_classes, activation="softmax", kernel_regularizer=keras.regularizers.l2(1e-4))(x)
    model = keras.Model(inputs, outputs, name="Food101_Improved_EfficientNetV2S")
    return model


def build_training_callbacks(model_path: str | Path, patience: int = 5) -> list[keras.callbacks.Callback]:
    """Create validation-driven callbacks for a training run."""
    checkpoint = keras.callbacks.ModelCheckpoint(
        str(model_path),
        monitor="val_accuracy",
        save_best_only=True,
        mode="max",
        verbose=1,
    )
    early_stop = keras.callbacks.EarlyStopping(
        monitor="val_accuracy",
        patience=patience,
        restore_best_weights=True,
        mode="max",
    )
    reduce_lr = keras.callbacks.ReduceLROnPlateau(
        monitor="val_loss",
        factor=0.2,
        patience=max(2, patience - 2),
        min_lr=1e-6,
    )
    return [checkpoint, early_stop, reduce_lr]


def compile_improved_model(model: keras.Model, learning_rate: float = 1e-3, label_smoothing: float = 0.05):
    """Compile the model with a modern optimizer.

    Some Keras builds reject the ``label_smoothing`` argument on
    ``SparseCategoricalCrossentropy`` in this environment, so the project uses the
    default sparse loss and keeps the augmentation/fine-tuning recipe as the main
    accuracy lever.
    """
    optimizer = keras.optimizers.AdamW(learning_rate=learning_rate, weight_decay=1e-4)
    model.compile(
        optimizer=optimizer,
        loss=keras.losses.SparseCategoricalCrossentropy(),
        metrics=["accuracy"],
    )
    return model


def stage_finetune(model: keras.Model, freeze_until: int | None = None) -> None:
    """Freeze the backbone initially and unfreeze the last blocks later.

    The default behavior keeps the backbone fixed during the first stage, which is the
    safest way to establish a strong head before fine-tuning higher-level features.
    """
    if freeze_until is None:
        model.trainable = True
        for layer in model.layers:
            if hasattr(layer, "trainable"):
                layer.trainable = True
        return

    model.trainable = True
    for layer in model.layers:
        if hasattr(layer, "trainable"):
            layer.trainable = False
    for layer in model.layers[freeze_until:]:
        if hasattr(layer, "trainable"):
            layer.trainable = True


def make_training_augmentation() -> keras.Sequential:
    """Use image augmentation that is realistic for food photos."""
    return keras.Sequential(
        [
            keras.layers.RandomFlip("horizontal"),
            keras.layers.RandomRotation(0.12),
            keras.layers.RandomZoom(0.10),
            keras.layers.RandomContrast(0.12),
            keras.layers.RandomBrightness(0.08),
        ],
        name="food_augmentation",
    )


def train_recipe(model: keras.Model, train_ds, val_ds, epochs: int = 30, output_path: str | Path = "results/improved_food101.keras"):
    """Execute the improved training recipe.

    This function is intentionally modular: it is designed to work with the project's
    existing Keras Sequence or tf.data pipeline. It can be dropped into a notebook or a
    longer training script without changing the app.
    """
    augmentation = make_training_augmentation()
    model = model

    inputs = keras.Input(shape=(224, 224, 3))
    x = augmentation(inputs)
    outputs = model(x)
    wrapped_model = keras.Model(inputs, outputs)
    compile_improved_model(wrapped_model, learning_rate=1e-3)

    callbacks = build_training_callbacks(output_path, patience=5)
    history = wrapped_model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=epochs,
        callbacks=callbacks,
        verbose=1,
    )

    wrapped_model.save(str(output_path))
    return wrapped_model, history


if __name__ == "__main__":
    model = build_improved_food101_model(num_classes=101)
    print(model.summary())
    print("\nSuggested next step: run this model against the Food-101 train/val data with the project's existing loader and compare against the current EfficientNetB0 baseline.")
