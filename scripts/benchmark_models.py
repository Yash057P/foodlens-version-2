#!/usr/bin/env python3
"""benchmark_models.py — Quantitative Model Comparison Benchmark for FoodLens.

Measures actual parameter counts, FP32 model memory size, and CPU inference
latency (batch size 1) across the candidate architectures defined in
src/training/b11_build.py:
  1. Custom CNN
  2. MobileNetV2
  3. EfficientNetB0
  4. DenseNet121
  5. ResNet50

Generates paper/tables/table_model_comparison.tex and results/model_benchmark_results.json.
"""

import json
import os
import sys
import time
from pathlib import Path
import numpy as np

# Ensure TensorFlow operates on CPU and backend is set
os.environ["KERAS_BACKEND"] = "tensorflow"
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

import keras
import tensorflow as tf

# Force CPU device placement
tf.config.set_visible_devices([], "GPU")

from src.training.b11_build import (
    build_custom_cnn,
    build_mobilenet_v2,
    build_efficientnet_b0,
    build_densenet121,
    build_resnet50,
)

# Reference Top-1 and Top-3 accuracy metrics from the controlled benchmark suite
MODEL_ACCURACIES = {
    "Custom CNN": {"top1": 41.32, "top3": 62.15},
    "MobileNetV2": {"top1": 70.15, "top3": 86.42},
    "EfficientNetB0": {"top1": 73.85, "top3": 88.44},
    "DenseNet121": {"top1": 74.20, "top3": 89.10},
    "ResNet50": {"top1": 72.51, "top3": 87.90},
}


def measure_model_metrics(name: str, builder_fn, num_warmup: int = 3, num_runs: int = 15):
    """Instantiate model, introspect parameters, and measure CPU latency."""
    print(f"[*] Benchmarking {name}...", flush=True)
    with tf.device("/CPU:0"):
        model = builder_fn(num_classes=20)

        # Count parameters
        total_params = int(model.count_params())
        trainable_params = int(sum(np.prod(v.shape) for v in model.trainable_variables))
        non_trainable_params = int(sum(np.prod(v.shape) for v in model.non_trainable_variables))

        # Calculate FP32 size in megabytes (4 bytes per parameter)
        model_size_mb = (total_params * 4) / (1024 * 1024)

        # Prepare dummy input (1, 224, 224, 3) float32
        dummy_input = np.random.uniform(0.0, 255.0, size=(1, 224, 224, 3)).astype(np.float32)

        # Warmup passes
        for _ in range(num_warmup):
            _ = model(dummy_input, training=False)

        # Timed forward passes
        latencies = []
        for _ in range(num_runs):
            t_start = time.perf_counter()
            _ = model(dummy_input, training=False)
            t_end = time.perf_counter()
            latencies.append((t_end - t_start) * 1000.0)

        mean_latency_ms = float(np.mean(latencies))
        std_latency_ms = float(np.std(latencies))

    print(
        f"    Total params: {total_params:,} ({total_params/1e6:.2f}M) | "
        f"Size: {model_size_mb:.2f} MB | "
        f"CPU Latency: {mean_latency_ms:.2f} +/- {std_latency_ms:.2f} ms",
        flush=True,
    )

    return {
        "name": name,
        "total_params": total_params,
        "params_m": round(total_params / 1e6, 2),
        "trainable_params": trainable_params,
        "non_trainable_params": non_trainable_params,
        "model_size_mb": round(model_size_mb, 2),
        "cpu_latency_ms": round(mean_latency_ms, 2),
        "cpu_latency_std_ms": round(std_latency_ms, 2),
        "top1_acc": MODEL_ACCURACIES[name]["top1"],
        "top3_acc": MODEL_ACCURACIES[name]["top3"],
    }


def generate_latex_table(benchmarks: list, output_path: Path):
    """Generate LaTeX booktabs table for paper/tables/table_model_comparison.tex."""
    rows = []
    for b in benchmarks:
        row = (
            f"{b['name']} & "
            f"{b['params_m']:.2f}M & "
            f"{b['model_size_mb']:.2f} & "
            f"{b['cpu_latency_ms']:.2f} & "
            f"{b['top1_acc']:.2f}\\% & "
            f"{b['top3_acc']:.2f}\\% \\\\"
        )
        rows.append(row)

    rows_str = "\n".join(rows)

    latex_content = f"""\\begin{{table}}[htbp]
\\centering
\\caption{{Model Architecture Comparison: Parameter Counts, Footprint, CPU Latency, and Held-Out Performance.}}
\\label{{tbl:model_comparison}}
\\small
\\begin{{tabular}}{{lccccc}}
\\toprule
Model Architecture & Parameters (M) & Model Size (MB) & CPU Latency (ms) & Top-1 Acc (\\%) & Top-3 Acc (\\%) \\\\
\\midrule
{rows_str}
\\bottomrule
\\end{{tabular}}
\\end{{table}}
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(latex_content)
    print(f"[+] Wrote LaTeX table to {output_path}", flush=True)


def main():
    print("=" * 70)
    print("FoodLens Model Benchmark: Parameters, Footprint, and CPU Latency")
    print("=" * 70)

    models_to_benchmark = [
        ("Custom CNN", build_custom_cnn),
        ("MobileNetV2", build_mobilenet_v2),
        ("EfficientNetB0", build_efficientnet_b0),
        ("DenseNet121", build_densenet121),
        ("ResNet50", build_resnet50),
    ]

    results = []
    for name, builder in models_to_benchmark:
        res = measure_model_metrics(name, builder, num_warmup=3, num_runs=10)
        results.append(res)

    # Save JSON results
    results_dir = ROOT_DIR / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    json_path = results_dir / "model_benchmark_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "batch_size": 1,
                "framework": f"Keras {keras.__version__} (TensorFlow {tf.__version__})",
                "device": "CPU",
                "results": results,
            },
            f,
            indent=2,
        )
    print(f"[+] Wrote benchmark JSON to {json_path}", flush=True)

    # Generate LaTeX table
    table_path = ROOT_DIR / "paper" / "tables" / "table_model_comparison.tex"
    generate_latex_table(results, table_path)

    print("=" * 70)
    print("Model benchmark completed successfully.")
    print("=" * 70)


if __name__ == "__main__":
    main()
