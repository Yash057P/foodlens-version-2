"""Fit scalar temperature calibration from held-out Food-101 probabilities."""
import argparse
import json
from pathlib import Path

import numpy as np


def softmax(logits):
    shifted = logits - logits.max(axis=1, keepdims=True)
    values = np.exp(shifted)
    return values / values.sum(axis=1, keepdims=True)


def nll(probs, labels):
    return float(-np.log(np.clip(probs[np.arange(len(labels)), labels], 1e-12, 1)).mean())


def ece(probs, labels, bins=15):
    confidence = probs.max(axis=1)
    correct = probs.argmax(axis=1) == labels
    total = 0.0
    for lower in np.linspace(0, 1, bins, endpoint=False):
        upper = lower + 1 / bins
        mask = (confidence >= lower) & (confidence < upper if upper < 1 else confidence <= upper)
        if mask.any():
            total += mask.mean() * abs(float(correct[mask].mean()) - float(confidence[mask].mean()))
    return float(total)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", required=True, help="NPZ containing probs and Y or labels")
    parser.add_argument("--output", default="webapp/data/calibration.json")
    args = parser.parse_args()
    data = np.load(args.predictions)
    probs = np.asarray(data["probs"], dtype=np.float64)
    label_key = "Y" if "Y" in data else "labels"
    labels = np.asarray(data[label_key]).astype(int).reshape(-1)
    if probs.ndim != 2 or len(probs) != len(labels):
        raise ValueError("Expected probs[N,C] and labels[N].")
    logits = np.log(np.clip(probs, 1e-12, 1))
    candidates = np.linspace(0.5, 4.0, 701)
    losses = np.array([nll(softmax(logits / value), labels) for value in candidates])
    temperature = float(candidates[losses.argmin()])
    calibrated = softmax(logits / temperature)
    result = {
        "status": "fitted",
        "method": "scalar_temperature_scaling",
        "temperature": round(temperature, 6),
        "samples": int(len(labels)),
        "nll_before": round(nll(probs, labels), 6),
        "nll_after": round(nll(calibrated, labels), 6),
        "ece_before": round(ece(probs, labels), 6),
        "ece_after": round(ece(calibrated, labels), 6),
        "source": str(Path(args.predictions)),
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
