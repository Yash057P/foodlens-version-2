"""Export user-approved FoodLens corrections into a reviewable training manifest."""
import argparse
import csv
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--feedback", default="webapp/feedback/feedback.jsonl")
    parser.add_argument("--output", default="artifacts/feedback_manifest.csv")
    args = parser.parse_args()
    source = Path(args.feedback)
    records = []
    skipped = 0
    if source.exists():
        for line in source.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            image_path = row.get("image_path")
            image = source.parent / image_path if image_path else None
            if row.get("source") != "user" or not image or not image.exists():
                skipped += 1
                continue
            records.append({
                "image": str(image.resolve()),
                "label": row["corrected_class"],
                "predicted_label": row["predicted_class"],
                "confidence": row["confidence"],
                "timestamp": row["timestamp"],
                "review_status": "pending_human_review",
            })
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["image", "label", "predicted_label", "confidence", "timestamp", "review_status"])
        writer.writeheader()
        writer.writerows(records)
    print(f"Exported {len(records)} opted-in samples; skipped {skipped} metadata-only/automated/missing-image records.")
    print("Human review is required before fine-tuning.")


if __name__ == "__main__":
    main()
