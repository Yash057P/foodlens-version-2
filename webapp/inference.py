"""Model inference wrapper for FoodLens.

Loads the trained EfficientNetB0 model once and exposes single-image prediction.
Preprocessing MUST match training exactly: JPEG decode -> bilinear resize to
(224,224) (aspect-ratio squish, as tf.image.resize) -> float32 in [0,255] with
NO extra normalization (the training notebook used raw pixels).
"""
import base64
import io
import json
import sys
import threading
import time
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # repo root

import keras

IMG_SIZE = 224
MODEL_PATH = Path(__file__).resolve().parent / "models" / "best_model.keras"
CLASSES_PATH = Path(__file__).resolve().parent / "data" / "classes_101.json"
INGREDIENTS_PATH = Path(__file__).resolve().parent / "data" / "ingredients.json"
CALIBRATION_PATH = Path(__file__).resolve().parent / "data" / "calibration.json"

WARN_LOW_CONFIDENCE = 0.45      # top-1 probability below this -> warn
WARN_TIE_DELTA = 0.10           # top1-top2 gap smaller than this -> "ambiguous"


class FoodLensModel:
    def __init__(self) -> None:
        load_started = time.perf_counter()
        self.model = keras.models.load_model(str(MODEL_PATH), compile=False)
        self.class_map = json.loads(CLASSES_PATH.read_text(encoding="utf-8"))
        self.ingredients = json.loads(INGREDIENTS_PATH.read_text(encoding="utf-8"))["classes"]
        calibration = json.loads(CALIBRATION_PATH.read_text(encoding="utf-8")) if CALIBRATION_PATH.exists() else {}
        self.temperature = float(calibration.get("temperature", 1.0))
        self.calibration = calibration
        self.model_name = "EfficientNetB0"
        self.model_version = "1.0.0"
        self.class_count = len(self.class_map["index_to_name"])
        self.parameter_count = int(self.model.count_params())
        self.backend = keras.backend.backend()
        self._predict_lock = threading.Lock()
        # Run one real forward pass at startup so the first viva prediction does
        # not pay graph tracing and kernel initialization costs.
        # Keep the warmup and inference passes at batch size 1 to avoid a
        # large activation-memory spike on small production instances.
        warmup_batch = np.zeros((1, IMG_SIZE, IMG_SIZE, 3), dtype=np.float32)
        with self._predict_lock:
            _ = keras.ops.convert_to_numpy(self.model(warmup_batch, training=False))
        self.load_time_ms = round((time.perf_counter() - load_started) * 1000, 1)
        self.ready = True
        print(f"FoodLens model loaded and warmed in {self.load_time_ms} ms", flush=True)

    def predict_bytes(self, raw: bytes, use_tta: bool = True, confidence_threshold: float | None = None) -> dict:
        started = time.perf_counter()
        img = Image.open(io.BytesIO(raw)).convert("RGB")
        quality = self._image_quality(img)
        
        # 1. Base Image
        img_base = img.resize((IMG_SIZE, IMG_SIZE), Image.BILINEAR)
        x_base = np.asarray(img_base, dtype=np.float32)
        
        # 2. Horizontally Flipped Image
        flip_attr = getattr(Image, 'Transpose', Image)
        img_flip = img_base.transpose(flip_attr.FLIP_LEFT_RIGHT)
        x_flip = np.asarray(img_flip, dtype=np.float32)
        
        # 3. Zoomed/Cropped Image (10% center crop)
        w, h = img.size
        cw, ch = int(w * 0.1), int(h * 0.1)
        img_crop = img.crop((cw, ch, w - cw, h - ch)).resize((IMG_SIZE, IMG_SIZE), Image.BILINEAR)
        x_crop = np.asarray(img_crop, dtype=np.float32)
        
        variants = [x_base, x_flip, x_crop] if use_tta else [x_base]
        # Run TTA views sequentially. This preserves the same probability
        # average while using much less peak memory than a three-image batch.
        with self._predict_lock:
            preds = np.stack([
                keras.ops.convert_to_numpy(
                    self.model(np.expand_dims(variant, 0), training=False)
                )[0]
                for variant in variants
            ])
        
        # Average the probabilities across the 3 augmented versions
        probs = np.mean(preds, axis=0)
        if self.calibration.get("status") == "fitted" and self.temperature > 0:
            logits = np.log(np.clip(probs.astype(np.float64), 1e-12, 1.0)) / self.temperature
            logits -= logits.max()
            probs = np.exp(logits)
            probs /= probs.sum()
        
        threshold = WARN_LOW_CONFIDENCE if confidence_threshold is None else max(0.05, min(0.95, confidence_threshold))
        packaged = self._package(probs, threshold)
        packaged["image_quality"] = quality
        packaged["warnings"] = quality["warnings"] + packaged["warnings"]
        packaged["inference"] = {
            "model": self.model_name,
            "model_version": self.model_version,
            "backend": self.backend,
            "classes": self.class_count,
            "input_shape": [IMG_SIZE, IMG_SIZE, 3],
            "tta_views": len(variants),
            "tta_enabled": use_tta,
            "confidence_threshold": threshold,
            "latency_ms": round((time.perf_counter() - started) * 1000, 1),
        }
        return packaged

    def metadata(self) -> dict:
        """Return safe model facts for health checks and the viva UI."""
        return {
            "name": self.model_name,
            "version": self.model_version,
            "architecture": "EfficientNetB0 transfer learning",
            "backend": self.backend,
            "classes": self.class_count,
            "parameters": self.parameter_count,
            "input_shape": [IMG_SIZE, IMG_SIZE, 3],
            "tta_views": 3,
            "confidence_threshold": WARN_LOW_CONFIDENCE,
            "ambiguity_margin": WARN_TIE_DELTA,
            "calibration": {
                "status": self.calibration.get("status", "not_fitted"),
                "method": self.calibration.get("method"),
                "temperature": self.temperature,
                "fit_split": self.calibration.get("fit_split"),
                "fit_samples": self.calibration.get("fit_samples"),
                "evaluation_split": self.calibration.get("evaluation_split"),
                "samples": self.calibration.get("samples"),
                "ece_before": self.calibration.get("ece_before"),
                "ece_after": self.calibration.get("ece_after"),
            },
            "load_time_ms": self.load_time_ms,
            "ready": self.ready,
        }

    def _package(self, probs: np.ndarray, confidence_threshold: float = WARN_LOW_CONFIDENCE) -> dict:
        idx_to_name = self.class_map["index_to_name"]
        order = np.argsort(probs)[::-1][:3]
        top = [
            {"rank": r + 1, "class": idx_to_name[str(i)], "name": idx_to_name[str(i)].replace("_", " ").title(), "prob": round(float(probs[i]), 4)}
            for r, i in enumerate(order)
        ]
        warnings = self._warnings(probs, order, confidence_threshold)
        safe_probs = np.clip(probs.astype(np.float64), 1e-12, 1.0)
        normalized_entropy = float(-np.sum(safe_probs * np.log(safe_probs)) / np.log(len(safe_probs)))
        margin = float(probs[order[0]] - probs[order[1]]) if len(order) > 1 else float(probs[order[0]])
        lead = top[0]
        info = self.ingredients.get(top[0]["class"], {})
        return {
            "top": top,
            "warnings": warnings,
            "lead_class": lead["class"],
            "lead_name": lead["name"],
            "ingredients": info,
            "uncertainty": {
                "normalized_entropy": round(normalized_entropy, 4),
                "top1_margin": round(margin, 4),
                "interpretation": "low" if normalized_entropy < 0.35 else "moderate" if normalized_entropy < 0.65 else "high",
            },
            "status": "ok",
        }

    def _warnings(self, probs: np.ndarray, order: np.ndarray, confidence_threshold: float) -> list[dict]:
        warnings = []
        p1 = float(probs[order[0]])
        if p1 < confidence_threshold:
            warnings.append({
                "level": "warning",
                "type": "low_confidence",
                "message": f"We're only {p1:.0%} confident. Try a brighter, closer photo and confirm the dish before relying on its food details.",
            })
        if len(order) > 1:
            gap = float(probs[order[0]] - probs[order[1]])
            if abs(gap) < WARN_TIE_DELTA:
                warnings.append({
                    "level": "info",
                    "type": "ambiguous",
                    "message": "Two dishes look similarly likely. Compare the matches and use your own judgement.",
                })
        return warnings

    @staticmethod
    def _image_quality(img: Image.Image) -> dict:
        gray = np.asarray(img.convert("L"), dtype=np.float32)
        brightness = float(gray.mean())
        edge_energy = float(np.mean(np.abs(np.diff(gray, axis=0))) + np.mean(np.abs(np.diff(gray, axis=1))))
        width, height = img.size
        warnings = []
        if min(width, height) < IMG_SIZE:
            warnings.append({"level": "info", "type": "small_image", "message": "This image is smaller than the model input and may lose detail when resized."})
        if brightness < 45:
            warnings.append({"level": "warning", "type": "too_dark", "message": "The photo is very dark. Brighter lighting may improve recognition."})
        elif brightness > 220:
            warnings.append({"level": "info", "type": "overexposed", "message": "The photo appears overexposed and may hide food texture."})
        if edge_energy < 5.0:
            warnings.append({"level": "warning", "type": "possible_blur", "message": "The photo has very little edge detail and may be blurred."})
        if max(width, height) / max(1, min(width, height)) > 3:
            warnings.append({"level": "info", "type": "extreme_aspect", "message": "A tighter crop around the dish may improve recognition."})
        return {"width": width, "height": height, "brightness": round(brightness, 1), "edge_energy": round(edge_energy, 2), "warnings": warnings}

    def gradcam_bytes(self, raw: bytes, class_name: str | None = None) -> dict:
        """Generate a Grad-CAM overlay from the deployed EfficientNet feature map."""
        if self.backend != "tensorflow":
            raise RuntimeError("Grad-CAM currently requires the TensorFlow backend.")
        import tensorflow as tf

        original = Image.open(io.BytesIO(raw)).convert("RGB")
        resized = original.resize((IMG_SIZE, IMG_SIZE), Image.BILINEAR)
        batch = np.expand_dims(np.asarray(resized, dtype=np.float32), 0)
        idx_to_name = self.class_map["index_to_name"]
        name_to_idx = {name: int(index) for index, name in idx_to_name.items()}
        backbone = self.model.get_layer("efficientnetb0")

        with self._predict_lock:
            tensor = tf.convert_to_tensor(batch)
            with tf.GradientTape() as tape:
                features = backbone(tensor, training=False)
                tape.watch(features)
                output = features
                for layer in self.model.layers[2:]:
                    output = layer(output, training=False)
                target_index = name_to_idx.get(class_name) if class_name else int(tf.argmax(output[0]))
                if target_index is None:
                    raise ValueError("Unknown target class for Grad-CAM.")
                score = output[:, target_index]
            gradients = tape.gradient(score, features)

        weights = tf.reduce_mean(gradients, axis=(0, 1, 2))
        heatmap = tf.reduce_sum(features[0] * weights, axis=-1)
        heatmap = tf.maximum(heatmap, 0)
        maximum = tf.reduce_max(heatmap)
        heatmap = tf.where(maximum > 0, heatmap / maximum, heatmap)
        heatmap_img = Image.fromarray(np.uint8(255 * heatmap.numpy())).resize(original.size, Image.BILINEAR)
        heat = np.asarray(heatmap_img, dtype=np.float32) / 255.0
        base = np.asarray(original, dtype=np.float32)
        colour = np.stack([255 * heat, 165 * np.sqrt(heat), 40 * (1 - heat)], axis=-1)
        alpha = (0.12 + 0.48 * heat)[..., None]
        overlay = Image.fromarray(np.uint8(np.clip(base * (1 - alpha) + colour * alpha, 0, 255)))
        encoded = io.BytesIO()
        overlay.save(encoded, format="JPEG", quality=90)
        return {
            "status": "ok",
            "class": idx_to_name[str(target_index)],
            "layer": "efficientnetb0 feature map (7x7x1280)",
            "method": "Grad-CAM",
            "overlay": "data:image/jpeg;base64," + base64.b64encode(encoded.getvalue()).decode("ascii"),
        }

    def ingredients_for(self, class_name: str) -> dict:
        return self.ingredients.get(class_name, {})


if __name__ == "__main__":
    m = FoodLensModel()
    # sanity: predict on a couple of local test images
    test_dir = Path(__file__).resolve().parents[1] / "data" / "extracted" / "food-101" / "images"
    for rel in ("pizza/100", "sushi/9"):
        img_p = test_dir / f"{rel}.jpg"
        if img_p.exists():
            out = m.predict_bytes(img_p.read_bytes())
            print(rel, "->", out["lead_name"], out["top"][0]["prob"], "warnings:", [w["type"] for w in out["warnings"]])
