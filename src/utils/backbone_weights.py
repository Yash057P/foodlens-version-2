"""Predownload Keras ImageNet backbone weights into the keras cache.

Same resume+retry downloader as the dataset (ISP drops long transfers). Files
are named exactly as keras file_utils expects, so keras.applications loaders
find them without re-downloading.
"""
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.utils.download import download_resumable

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

CACHE = Path.home() / ".keras" / "models"
CACHE.mkdir(parents=True, exist_ok=True)

WEIGHTS = [
    # (url, expected bytes)
    ("https://storage.googleapis.com/tensorflow/keras-applications/resnet/resnet50_weights_tf_dim_ordering_tf_kernels_notop.h5", 94_765_736),
    ("https://storage.googleapis.com/tensorflow/keras-applications/mobilenet_v2/mobilenetv2_weights_tf_dim_ordering_tf_kernels_1.0_224_no_top.h5", 14_224_656),
    ("https://storage.googleapis.com/tensorflow/keras-applications/densenet/densenet121_weights_tf_dim_ordering_tf_kernels_notop.h5", 32_321_048),
    ("https://storage.googleapis.com/keras-applications/efficientnet/efficientnetb0_notop.h5", 21_634_320),
]

if __name__ == "__main__":
    for url, size in WEIGHTS:
        download_resumable(url, CACHE / Path(url).name, size)
    print("ALL BACKBONE WEIGHTS READY", flush=True)