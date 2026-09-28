"""Model inference wrapper for FoodLens.

Loads the trained EfficientNetB0 model once and exposes single-image prediction.
Preprocessing MUST match training exactly: JPEG decode -> bilinear resize to
(224,224) (aspect-ratio squish, as tf.image.resize) -> float32 in [0,255] with
NO extra normalization (the training notebook used raw pixels).
"""
import io
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # repo root

import keras

IMG_SIZE = 224
MODEL_PATH = Path(__file__).resolve().parent / "models" / "best_model.keras"
CLASSES_PATH = Path(__file__).resolve().parent / "data" / "classes_101.json"
INGREDIENTS_PATH = Path(__file__).resolve().parent / "data" / "ingredients.json"

WARN_LOW_CONFIDENCE = 0.45      # top-1 probability below this -> warn
WARN_TIE_DELTA = 0.10           # top1-top2 gap smaller than this -> "ambiguous"


class FoodLensModel:
    def __init__(self) -> None:
        self.model = keras.models.load_model(str(MODEL_PATH), compile=False)
        self.class_map = json.loads(CLASSES_PATH.read_text(encoding="utf-8"))
        self.ingredients = json.loads(INGREDIENTS_PATH.read_text(encoding="utf-8"))["classes"]
        print("FoodLens model loaded", flush=True)

    def predict_bytes(self, raw: bytes) -> dict:
        img = Image.open(io.BytesIO(raw)).convert("RGB")
        
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
        
        # Batch TTA variations: (3, 224, 224, 3)
        x_batch = np.stack([x_base, x_flip, x_crop])
        
        # Forward pass on all variations
        preds = keras.ops.convert_to_numpy(self.model(x_batch))
        
        # Average the probabilities across the 3 augmented versions
        probs = np.mean(preds, axis=0)
        
        return self._package(probs)

    def _package(self, probs: np.ndarray) -> dict:
        idx_to_name = self.class_map["index_to_name"]
        order = np.argsort(probs)[::-1][:3]
        top = [
            {"rank": r + 1, "class": idx_to_name[str(i)], "name": idx_to_name[str(i)].replace("_", " ").title(), "prob": round(float(probs[i]), 4)}
            for r, i in enumerate(order)
        ]
        warnings = self._warnings(probs, order)
        lead = top[0]
        info = self.ingredients.get(top[0]["class"], {})
        return {
            "top": top,
            "warnings": warnings,
            "lead_class": lead["class"],
            "lead_name": lead["name"],
            "ingredients": info,
            "status": "ok",
        }

    def _warnings(self, probs: np.ndarray, order: np.ndarray) -> list[dict]:
        warnings = []
        p1 = float(probs[order[0]])
        if p1 < WARN_LOW_CONFIDENCE:
            warnings.append({
                "level": "warning",
                "type": "low_confidence",
                "message": f"Low confidence ({p1:.0%}): the photo may not be a clear food dish or may be blurred. Please retake with better lighting.",
            })
        if len(order) > 1:
            gap = float(probs[order[0]] - probs[order[1]])
            if abs(gap) < WARN_TIE_DELTA:
                warnings.append({
                    "level": "info",
                    "type": "ambiguous",
                    "message": "Two very similar predictions - the dish type is uncertain.",
                })
        return warnings

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