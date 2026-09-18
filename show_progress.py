"""Live download progress bars - run this in your own terminal:

    .venv\\Scripts\\python.exe show_progress.py

Shows Food-101 archive + backbone weights with an auto-refreshing bar.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import ARCHIVE_PATH, ARCHIVE_SIZE_BYTES

CACHE = Path.home() / ".keras" / "models"

TASKS = [
    ("Food-101 archive", ARCHIVE_PATH, ARCHIVE_SIZE_BYTES),
    ("ResNet50", CACHE / "resnet50_weights_tf_dim_ordering_tf_kernels_notop.h5", 94_765_736),
    ("MobileNetV2", CACHE / "mobilenetv2_weights_tf_dim_ordering_tf_kernels_1.0_224_no_top.h5", 14_224_656),
    ("DenseNet121", CACHE / "densenet121_weights_tf_dim_ordering_tf_kernels_notop.h5", 32_321_048),
    ("EfficientNetB0", CACHE / "efficientnetb0_notop.h5", 21_634_320),
]


def bar(label: str, done: int, total: int, width: int = 40) -> str:
    pct = min(100.0, 100.0 * done / total)
    filled = int(width * pct / 100)
    blocks = "#" * filled + "-" * (width - filled)
    return f"{label:<16} [{blocks}] {pct:5.1f}%  {done/1e6:6.1f}/{total/1e6:6.1f} MB"


def main() -> None:
    try:
        while True:
            lines = []
            for label, path, total in TASKS:
                done = path.stat().st_size if path.exists() else 0
                lines.append(bar(label, done, total))
            speed = _speed()
            sys.stdout.write("\033[F" * (len(lines)))  # noqa: UP012
            sys.stdout.write("\n".join(lines) + f"\nspeed: {speed:5.1f} MB/s (all workers)\n")
            sys.stdout.flush()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nstopped")


def _speed() -> float:
    samples = [(p, p.stat().st_size if p.exists() else 0) for _, p, _ in TASKS]
    time.sleep(1)
    samples2 = [(p, p.stat().st_size if p.exists() else 0) for _, p, _ in TASKS]
    delta = sum(a[1] - b[1] for a, b in zip(samples2, samples))
    return delta / (1024 * 1024)


if __name__ == "__main__":
    main()