"""Batch 2 - Acquire and inventory data.

Downloads Food-101 from the official ETH mirror (resume-capable + auto-retry),
verifies the archive size, and extracts only what we need: images/ and
meta/{train,test}.txt.
"""
import logging
import sys
import tarfile
import time

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2]))
from config import ARCHIVE_PATH, ARCHIVE_SIZE_BYTES, EXTRACTED_DIR, FOOD101_DIR, IMAGE_DIR
from src.utils.download import download_resumable

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("acquire")


def download() -> None:
    download_resumable("https://data.vision.ee.ethz.ch/cvl/food-101.tar.gz", ARCHIVE_PATH, ARCHIVE_SIZE_BYTES)


def extract() -> None:
    if IMAGE_DIR.exists() and any(IMAGE_DIR.iterdir()):
        log.info("Images already extracted: %s", IMAGE_DIR)
        return
    log.info("Extracting archive (this takes a few minutes)...")
    start = time.time()
    with tarfile.open(ARCHIVE_PATH, "r:gz") as tar:
        for member in tar.getmembers():
            name = member.name
            if name.startswith("food-101/images/") or name.startswith("food-101/meta/"):
                tar.extract(member, path=EXTRACTED_DIR)
    log.info("Extraction complete in %.1f min", (time.time() - start) / 60)


if __name__ == "__main__":
    download()
    extract()
    n_images = sum(1 for _ in IMAGE_DIR.rglob("*.jpg")) if IMAGE_DIR.exists() else 0
    log.info("DONE. image files: %d | train meta: %s | test meta: %s",
             n_images,
             (FOOD101_DIR / "meta" / "train.txt").is_file(),
             (FOOD101_DIR / "meta" / "test.txt").is_file())