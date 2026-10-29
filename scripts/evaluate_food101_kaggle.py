"""Evaluate the deployed FoodLens model on the official Food-101 test split.

Designed for Kaggle with datasets hari31416/food-101 and the private deployed
checkpoint dataset mounted. Writes full probabilities so calibration is auditable.
"""
from pathlib import Path
import csv
import json
import os
import random

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
import keras
import numpy as np
import tensorflow as tf
from scipy.optimize import minimize_scalar

IMG_SIZE = 224
BATCH_SIZE = 64
OUTPUT = Path("/kaggle/working/foodlens_evaluation")


def find_directory(name, expected_classes=101):
    for candidate in Path("/kaggle/input").glob(f"**/{name}"):
        if candidate.is_dir() and len([p for p in candidate.iterdir() if p.is_dir()]) == expected_classes:
            return candidate
    raise FileNotFoundError(f"Food-101 {name} directory was not found")


def find_file(filename):
    matches = list(Path("/kaggle/input").glob(f"**/{filename}"))
    if len(matches) != 1:
        raise FileNotFoundError(f"Expected exactly one {filename}, found {len(matches)}")
    return matches[0]


def load_image(path, label):
    image = tf.io.decode_jpeg(tf.io.read_file(path), channels=3)
    image = tf.image.resize(image, (IMG_SIZE, IMG_SIZE), method="bilinear")
    return tf.cast(image, tf.float32), label


def softmax(logits):
    shifted = logits - logits.max(axis=1, keepdims=True)
    exp = np.exp(shifted)
    return exp / exp.sum(axis=1, keepdims=True)


def nll(probabilities, labels):
    return float(-np.log(np.clip(probabilities[np.arange(len(labels)), labels], 1e-12, 1)).mean())


def ece(probabilities, labels, bins=15):
    confidence = probabilities.max(axis=1)
    correct = probabilities.argmax(axis=1) == labels
    result = 0.0
    for lower in np.linspace(0, 1, bins, endpoint=False):
        upper = lower + 1 / bins
        mask = (confidence >= lower) & (confidence < upper if upper < 1 else confidence <= upper)
        if mask.any():
            result += mask.mean() * abs(float(correct[mask].mean()) - float(confidence[mask].mean()))
    return float(result)


def main():
    images_dir = find_directory("images")
    test_list = find_file("test.txt")
    train_list = find_file("train.txt")
    model_path = find_file("best_model.keras")
    classes_path = find_file("classes_101.json")
    class_map = json.loads(classes_path.read_text(encoding="utf-8"))["index_to_name"]
    classes = [class_map[str(i)] for i in range(len(class_map))]
    class_to_index = {name: index for index, name in enumerate(classes)}
    def rows_from_list(list_path):
        result = []
        for relative in list_path.read_text(encoding="utf-8").splitlines():
            relative = relative.strip()
            if relative:
                class_name = relative.split("/")[0]
                result.append((str(images_dir / f"{relative}.jpg"), class_to_index[class_name]))
        return result

    rows = rows_from_list(test_list)
    train_rows = rows_from_list(train_list)
    indices = list(range(len(train_rows)))
    random.Random(42).shuffle(indices)
    validation_rows = [train_rows[i] for i in indices[int(0.85 * len(indices)):]]
    if len(validation_rows) != 11363:
        raise ValueError(f"Expected 11,363 seeded validation images, found {len(validation_rows)}")
    if len(rows) != 25250:
        raise ValueError(f"Expected 25,250 official test images, found {len(rows)}")
    def make_dataset(input_rows):
        input_paths = np.asarray([path for path, _ in input_rows], dtype=str)
        input_labels = np.asarray([label for _, label in input_rows], dtype=np.int32)
        data = tf.data.Dataset.from_tensor_slices((input_paths, input_labels)).map(load_image, num_parallel_calls=tf.data.AUTOTUNE).batch(BATCH_SIZE).prefetch(tf.data.AUTOTUNE)
        return data, input_paths, input_labels

    dataset, paths, labels = make_dataset(rows)
    validation_dataset, validation_paths, validation_labels = make_dataset(validation_rows)
    model = keras.models.load_model(model_path, compile=False)
    validation_probabilities = model.predict(validation_dataset, verbose=1)
    probabilities = model.predict(dataset, verbose=1)
    order = np.argsort(probabilities, axis=1)
    metrics = {f"top{k}": float(np.mean([labels[i] in order[i, -k:] for i in range(len(labels))])) for k in (1, 3, 5)}

    validation_logits = np.log(np.clip(validation_probabilities.astype(np.float64), 1e-12, 1))
    result = minimize_scalar(lambda value: nll(softmax(validation_logits / value), validation_labels), bounds=(0.5, 4.0), method="bounded")
    temperature = float(result.x)
    logits = np.log(np.clip(probabilities.astype(np.float64), 1e-12, 1))
    calibrated = softmax(logits / temperature)
    calibration = {
        "status": "fitted", "method": "scalar_temperature_scaling", "temperature": temperature,
        "fit_split": "seeded 15% Food-101 official training partition", "fit_samples": len(validation_labels),
        "evaluation_split": "Food-101 official test partition", "samples": len(labels),
        "validation_nll_before": nll(validation_probabilities, validation_labels),
        "validation_nll_after": nll(softmax(validation_logits / temperature), validation_labels),
        "nll_before": nll(probabilities, labels), "nll_after": nll(calibrated, labels),
        "ece_before": ece(probabilities, labels), "ece_after": ece(calibrated, labels),
    }

    predictions = probabilities.argmax(axis=1)
    matrix = np.zeros((len(classes), len(classes)), dtype=np.int64)
    np.add.at(matrix, (labels, predictions), 1)
    per_class = matrix.diagonal() / matrix.sum(axis=1)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(OUTPUT / "food101_test_predictions.npz", probs=probabilities.astype(np.float32), labels=labels, paths=paths)
    np.savez_compressed(OUTPUT / "food101_validation_predictions.npz", probs=validation_probabilities.astype(np.float32), labels=validation_labels, paths=validation_paths)
    (OUTPUT / "metrics.json").write_text(json.dumps({"dataset": "Food-101 official test split", "images": len(labels), **metrics}, indent=2), encoding="utf-8")
    (OUTPUT / "calibration.json").write_text(json.dumps(calibration, indent=2), encoding="utf-8")
    with (OUTPUT / "per_class_accuracy.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle); writer.writerow(["class", "correct", "total", "accuracy"])
        for index, name in enumerate(classes): writer.writerow([name, int(matrix[index, index]), int(matrix[index].sum()), float(per_class[index])])
    np.savetxt(OUTPUT / "confusion_matrix.csv", matrix, fmt="%d", delimiter=",")
    print(json.dumps({"metrics": metrics, "calibration": calibration}, indent=2))


if __name__ == "__main__":
    main()
