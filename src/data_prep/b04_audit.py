"""Batch 4 - Quality audit of the 20-class subset.

Scans every image referenced by the manifests: decode validity (PIL verify),
mode, dimensions, aspect ratio. Writes results/audit/audit.json and logs, plus
a dimensions histogram.
"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image, UnidentifiedImageError

from config import IMAGE_DIR, MANIFESTS_DIR, RESULTS_DIR

AUDIT_DIR = RESULTS_DIR / "audit"
AUDIT_DIR.mkdir(parents=True, exist_ok=True)


def scan() -> dict:
    stats = {
        "files": 0,
        "corrupt": [],
        "modes": Counter(),
        "widths": Counter(),
        "aspects": Counter(),
        "tiny_or_huge": [],
    }
    manifests = ["train.csv", "val.csv", "test.csv"]
    for name in manifests:
        path = MANIFESTS_DIR / name
        lines = path.read_text(encoding="utf-8").splitlines()[1:]
        for line in lines:
            cls, rel = line.split(",")
            stats["files"] += 1
            p = IMAGE_DIR / rel
            try:
                with Image.open(p) as im:
                    im.verify()
                with Image.open(p) as im:
                    w, h = im.size
                    stats["modes"][im.mode] += 1
                    stats["widths"][w] += 1
                    stats["aspects"][round(h / w, 2)] += 1
                    if w < 128 or h < 128:
                        stats["tiny_or_huge"].append(rel)
            except (UnidentifiedImageError, OSError, SyntaxError) as exc:
                stats["corrupt"].append((rel, str(exc)))
    return stats


def main() -> None:
    stats = scan()
    (MANIFESTS_DIR.parent).mkdir(parents=True, exist_ok=True)
    (AUDIT_DIR / "audit.json").write_text(
        json.dumps(
            {
                "files": stats["files"],
                "corrupt_count": len(stats["corrupt"]),
                "corrupt": stats["corrupt"][:50],
                "modes": dict(stats["modes"]),
                "top_widths": stats["widths"].most_common(8),
                "tiny_or_huge_count": len(stats["tiny_or_huge"]),
                "tiny_or_huge": stats["tiny_or_huge"][:20],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"audit: {stats['files']} files, {len(stats['corrupt'])} corrupt, {len(stats['tiny_or_huge'])} tiny/huge", flush=True)
    print("modes:", dict(stats["modes"]), flush=True)
    print("top width->count:", stats["widths"].most_common(8), flush=True)

    fig, ax = plt.subplots(figsize=(8, 3.2))
    widths, counts = zip(*stats["widths"].most_common(12))
    ax.bar([str(w) for w in widths], counts)
    ax.set_xlabel("width px")
    ax.set_ylabel("image count")
    ax.set_title("width distribution (top 12)")
    fig.tight_layout()
    fig.savefig(AUDIT_DIR / "widths.png", dpi=110)
    plt.close(fig)
    print("audit figures ->", AUDIT_DIR, flush=True)


if __name__ == "__main__":
    main()