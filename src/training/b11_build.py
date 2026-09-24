"""Batch 11 - Build all 5 model architectures.

Custom CNN is trained from scratch (no pretrained backbone). The four
pretrained backbones are loaded with imagenet weights and `include_top=False`,
followed by a GlobalAveragePooling2D + Dropout + Dense softmax classifier.

Every model is compiled with Adam + sparse-categorical-crossentropy so we can
pass integer labels directly from the loader without one-hot conversion.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import keras

from config import LEARNING_RATE, DROPOUT, SUBSET_CLASSES


def _classifier(x, num_classes: int = 20, dropout: float = DROPOUT):
    x = keras.layers.GlobalAveragePooling2D()(x)
    x = keras.layers.Dropout(dropout)(x)
    return keras.layers.Dense(num_classes, activation="softmax")(x)


def build_custom_cnn(num_classes: int = 20) -> keras.Model:
    inp = keras.Input((224, 224, 3))
    x = keras.layers.Conv2D(32, (3, 3), activation="relu", padding="same")(inp)
    x = keras.layers.MaxPooling2D()(x)
    x = keras.layers.Conv2D(64, (3, 3), activation="relu", padding="same")(x)
    x = keras.layers.MaxPooling2D()(x)
    x = keras.layers.Conv2D(128, (3, 3), activation="relu", padding="same")(x)
    x = keras.layers.MaxPooling2D()(x)
    x = _classifier(x, num_classes)
    return keras.Model(inp, x, name="CustomCNN")


def _transfer(base_fn, name: str, num_classes: int = 20) -> keras.Model:
    inp = keras.Input((224, 224, 3))
    base = base_fn(weights="imagenet", include_top=False, pooling="avg")
    base.trainable = False  # frozen head stage
    feat = base(inp, training=False)
    # pooling='avg' already gives 2D (None, features); skip GAP
    x = keras.layers.Dropout(DROPOUT)(feat)
    out = keras.layers.Dense(num_classes, activation="softmax")(x)
    return keras.Model(inp, out, name=name)


def build_resnet50(num_classes: int = 20) -> keras.Model:
    return _transfer(keras.applications.ResNet50, "ResNet50", num_classes)


def build_mobilenet_v2(num_classes: int = 20) -> keras.Model:
    return _transfer(keras.applications.MobileNetV2, "MobileNetV2", num_classes)


def build_densenet121(num_classes: int = 20) -> keras.Model:
    return _transfer(keras.applications.DenseNet121, "DenseNet121", num_classes)


def build_efficientnet_b0(num_classes: int = 20) -> keras.Model:
    return _transfer(keras.applications.EfficientNetB0, "EfficientNetB0", num_classes)


def build_efficientnet_b4(num_classes: int = 20) -> keras.Model:
    # B4 uses larger input resolution natively, but works with 224x224.
    # It has roughly 19M parameters vs B0's 5M parameters.
    return _transfer(keras.applications.EfficientNetB4, "EfficientNetB4", num_classes)


def build_efficientnet_v2s(num_classes: int = 20) -> keras.Model:
    # EfficientNetV2S converges faster and achieves higher top-1 accuracy on fine-grained tasks
    return _transfer(keras.applications.EfficientNetV2S, "EfficientNetV2S", num_classes)


MODEL_BUILDERS = {
    "CustomCNN": build_custom_cnn,
    "ResNet50": build_resnet50,
    "MobileNetV2": build_mobilenet_v2,
    "DenseNet121": build_densenet121,
    "EfficientNetB0": build_efficientnet_b0,
    "EfficientNetB4": build_efficientnet_b4,
    "EfficientNetV2S": build_efficientnet_v2s,
}


if __name__ == "__main__":
    for name, builder in MODEL_BUILDERS.items():
        m = builder()
        print(f"{name}: {m.count_params():,} params", flush=True)