"""Rank real food photographs for a reliable FoodLens viva demonstration.

The live Docker app must be running. This utility never changes or uploads the
photos permanently; it sends each candidate to the inference endpoint and
prints the highest-confidence examples for manual label verification.
"""

import argparse
from pathlib import Path

import requests


SUPPORTED = {".jpg", ".jpeg", ".png", ".webp"}


def score_image(path: Path, base_url: str) -> dict:
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    with path.open("rb") as image:
        response = requests.post(
            f"{base_url.rstrip('/')}/api/predict",
            files={"image": (path.name, image, mime)},
            timeout=120,
        )
    response.raise_for_status()
    prediction = response.json()
    lead = prediction["top"][0]
    return {
        "path": path,
        "label": lead["name"],
        "confidence": float(lead["prob"]),
        "warnings": [item["type"] for item in prediction.get("warnings", [])],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path, help="Folder containing real food photos")
    parser.add_argument("--url", default="http://127.0.0.1:5000", help="Running FoodLens URL")
    parser.add_argument("--top", type=int, default=6, help="Number of candidates to print")
    args = parser.parse_args()

    candidates = sorted(
        path for path in args.folder.rglob("*") if path.is_file() and path.suffix.lower() in SUPPORTED
    )
    if not candidates:
        raise SystemExit(f"No JPEG, PNG, or WebP images found under {args.folder}")

    results = []
    for path in candidates:
        try:
            results.append(score_image(path, args.url))
        except requests.RequestException as error:
            print(f"SKIP {path.name}: {error}")

    results.sort(key=lambda item: item["confidence"], reverse=True)
    print("\nBest viva candidates (verify the predicted label visually):")
    for item in results[: args.top]:
        warning_text = ", ".join(item["warnings"]) or "none"
        print(
            f"{item['confidence']:6.1%}  {item['label']:<28} "
            f"warnings={warning_text:<18} {item['path']}"
        )

    print("\nUse clear, correctly labelled candidates for the success demo.")
    print("Keep one low-confidence or non-food image to explain uncertainty rails.")


if __name__ == "__main__":
    main()
