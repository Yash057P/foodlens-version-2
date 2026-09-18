"""Resumable, retrying HTTP download with progress logging.

Used for the Food-101 archive and the Keras ImageNet backbone weights, because
the local ISP drops long transfers mid-stream.
"""
import logging
import time
from pathlib import Path

import requests

log = logging.getLogger("resumable_download")

CHUNK = 1024 * 1024
MAX_RETRIES = 50


def download_resumable(url: str, dest: Path, expected_size: int, max_retries: int = MAX_RETRIES) -> None:
    if expected_size and dest.exists() and dest.stat().st_size >= expected_size:
        log.info("already complete: %s", dest)
        return

    if dest.exists():
        size = dest.stat().st_size
        size = (size // CHUNK) * CHUNK  # drop a possibly-truncated tail
        if size:
            with open(dest, "r+b") as fh:
                fh.truncate(size)

    start = time.time()
    attempt = 0
    while True:
        attempt += 1
        existing = dest.stat().st_size if dest.exists() else 0
        if expected_size and existing >= expected_size:
            break
        headers = {"Range": f"bytes={existing}-"} if existing else {}
        log.info("attempt %d: %s from byte %d", attempt, dest.name, existing)
        last_pct = -1
        try:
            with requests.Session() as session:
                with session.get(url, headers=headers, stream=True, timeout=(30, 30)) as resp:
                    resp.raise_for_status()
                    mode = "ab" if existing else "wb"
                    with open(dest, mode) as fh:
                        for chunk in resp.iter_content(chunk_size=CHUNK):
                            if chunk:
                                fh.write(chunk)
                                if expected_size:
                                    done = fh.tell()
                                    pct = int(100 * done / expected_size)
                                    if pct % 5 == 0 and pct != last_pct:
                                        last_pct = pct
                                        log.info("  %s %.1f%%", dest.name, 100 * done / expected_size)
        except Exception as exc:
            log.error("attempt %d failed for %s: %s", attempt, dest.name, exc)
            if attempt >= max_retries:
                raise
            time.sleep(5)
            continue

    if expected_size and dest.stat().st_size < expected_size:
        raise SystemExit(f"incomplete: {dest}")
    log.info("done: %s (%.1f MB, %.1f min)", dest.name, dest.stat().st_size / (1024 * 1024), (time.time() - start) / 60)