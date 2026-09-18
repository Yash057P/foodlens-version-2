"""Ensure all backbone ImageNet weights are present, self-healing.

The local ISP intermittently drops storage.googleapis.com transfers and even
returns 404 on retry, so we let keras download each weight file itself inside a
retry loop, deleting any partial file between attempts.
"""
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import keras

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("ensure_backbones")
logging.getLogger().setLevel(logging.INFO)

CACHE = Path.home() / ".keras" / "models"

APP_MODELS = [
    ("ResNet50", keras.applications.ResNet50, "resnet50_weights_tf_dim_ordering_tf_kernels_notop.h5"),
    ("MobileNetV2", keras.applications.MobileNetV2, "mobilenet_v2_weights_tf_dim_ordering_tf_kernels_1.0_224_no_top.h5"),
    ("DenseNet121", keras.applications.DenseNet121, "densenet121_weights_tf_dim_ordering_tf_kernels_notop.h5"),
    ("EfficientNetB0", keras.applications.EfficientNetB0, "efficientnetb0_notop.h5"),
]

MAX_ATTEMPTS = 40


def ensure(base_model, fname: str) -> None:
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            # keras.get_file skips download if a full file is already cached
            base_model(weights="imagenet", include_top=False, input_shape=(224, 224, 3))
            log.info("OK %-12s", base_model.__name__)
            return
        except Exception as exc:
            partial = CACHE / fname
            if partial.exists():
                partial.unlink()
            log.warning("attempt %d for %s failed: %s", attempt, base_model.__name__, exc)
            time.sleep(3 + attempt)
    raise RuntimeError(f"could not fetch weights for {base_model.__name__}")


if __name__ == "__main__":
    for label, fn, fname in APP_MODELS:
        log.info("=== %s ===", label)
        ensure(fn, fname)
    print("ALL BACKBONE WEIGHTS READY", flush=True)