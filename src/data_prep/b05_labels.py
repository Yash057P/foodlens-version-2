"""Batch 5 - Build the class label mapping.

Creates a stable JSON mapping between integer indices and the 20 class names,
so every model and the Streamlit app share one index<->name contract.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from config import MANIFESTS_DIR, SUBSET_CLASSES

OUT = MANIFESTS_DIR / "labels.json"


def main() -> None:
    labels = {i: name for i, name in enumerate(sorted(SUBSET_CLASSES))}
    index_to_name = {str(i): name for i, name in labels.items()}
    payload = {
        "num_classes": len(labels),
        "index_to_name": index_to_name,
        "name_to_index": {name: i for i, name in labels.items()},
    }
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {OUT} ({len(labels)} classes)", flush=True)


if __name__ == "__main__":
    main()