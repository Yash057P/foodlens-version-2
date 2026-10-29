"""Convert the trained Keras model to a portable FP16 TFLite artifact."""
import argparse
from pathlib import Path

import tensorflow as tf


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", default="artifacts/foodlens_fp16.tflite")
    args = parser.parse_args()
    model_path = Path(args.model)
    output = Path(args.output)
    model = tf.keras.models.load_model(model_path, compile=False)
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.target_spec.supported_types = [tf.float16]
    converted = converter.convert()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(converted)
    print(f"Wrote {output} ({len(converted) / 1024 / 1024:.2f} MiB)")
    print(f"Source model: {model_path.stat().st_size / 1024 / 1024:.2f} MiB")


if __name__ == "__main__":
    main()
