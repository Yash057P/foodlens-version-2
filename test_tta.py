import sys
import io
from pathlib import Path
from PIL import Image

# 1. Create a dummy image
img = Image.new("RGB", (300, 300), color=(255, 100, 100))
img_byte_arr = io.BytesIO()
img.save(img_byte_arr, format="JPEG")
raw_bytes = img_byte_arr.getvalue()
print("Generated local test image in memory.")

# 2. Test the inference engine with TTA
sys.path.insert(0, str(Path("webapp").resolve()))
try:
    from inference import FoodLensModel
    print("Loading model...")
    model = FoodLensModel()
    print("Running TTA inference...")
    result = model.predict_bytes(raw_bytes)

    print("\n--- INFERENCE RESULT ---")
    print("Lead Class:", result["lead_name"])
    for item in result["top"]:
        print(f"{item['name']}: {item['prob']*100:.2f}%")
    print("Status:", result["status"])
    print("Warnings:", result["warnings"])
    print("\nSUCCESS: The TTA engine is working perfectly!")
except Exception as e:
    import traceback
    print("\nERROR:")
    traceback.print_exc()
