"""High-performance parallel chunk downloader for DevInstaller.

Features:
- Multi-threaded byte-range chunk download (HTTP 206 Partial Content).
- Non-blocking pre-allocated file streaming with thread-isolated file pointers.
- Live progress reporting (percentage, downloaded bytes, total bytes).
- Graceful fallback to single-stream download when byte ranges are unsupported.
- Clean cancellation support without leaving locked handles.
"""

from __future__ import annotations

import os
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable, Optional

from udm.logger import logger

_DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36 DevInstaller"
)

# Sent on every request: disabling transparent compression keeps Content-Length
# and byte-range math exact (a gzipped response would report a different length
# than the bytes we seek/write, corrupting parallel chunk assembly).
_BASE_HEADERS = {"User-Agent": _DEFAULT_USER_AGENT, "Accept-Encoding": "identity"}


def _probe_url(url: str, custom_headers: dict | None = None) -> tuple[int, bool]:
    """Probe the remote URL to check Content-Length and byte-range support.

    Returns:
        (total_size_in_bytes, supports_byte_ranges)
    """
    req_headers = {**_BASE_HEADERS, "Range": "bytes=0-0"}
    if custom_headers:
        req_headers.update(custom_headers)

    req = urllib.request.Request(url, headers=req_headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            if res.status == 206:
                content_range = res.headers.get("Content-Range", "")
                if "/" in content_range:
                    try:
                        total = int(content_range.rsplit("/", 1)[1].strip())
                        return total, True
                    except ValueError:
                        pass
            total = int(res.headers.get("Content-Length", 0))
            accept_ranges = res.headers.get("Accept-Ranges", "").lower()
            return total, ("bytes" in accept_ranges)
    except Exception as e:
        logger.debug(f"Range probe returned exception (will attempt standard probe): {e}")

    # Fallback to standard HEAD/GET probe
    try:
        head_headers = dict(_BASE_HEADERS)
        if custom_headers:
            head_headers.update(custom_headers)
        req = urllib.request.Request(url, headers=head_headers)
        with urllib.request.urlopen(req, timeout=15) as res:
            total = int(res.headers.get("Content-Length", 0))
            accept_ranges = res.headers.get("Accept-Ranges", "").lower()
            return total, ("bytes" in accept_ranges)
    except Exception as e:
        logger.warning(f"Standard probe failed for {url}: {e}")
        return 0, False


def _download_chunk(
    url: str,
    dest_path: str,
    start: int,
    end: int,
    progress_lock: threading.Lock,
    progress_tracker: dict,
    progress_callback: Optional[Callable[[int, int, int], None]],
    cancel_event: Optional[threading.Event],
    custom_headers: dict | None = None,
    block_size: int = 131072,  # 128KB buffer
) -> bool:
    """Download a specific byte range directly into the pre-allocated file."""
    headers = {
        **_BASE_HEADERS,
        "Range": f"bytes={start}-{end}",
    }
    if custom_headers:
        headers.update(custom_headers)

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as res, open(dest_path, "r+b") as f:
            f.seek(start)
            current_pos = start
            while current_pos <= end:
                if cancel_event and cancel_event.is_set():
                    return False
                to_read = min(block_size, end - current_pos + 1)
                buf = res.read(to_read)
                if not buf:
                    break
                f.write(buf)
                chunk_len = len(buf)
                current_pos += chunk_len

                with progress_lock:
                    progress_tracker["downloaded"] += chunk_len
                    downloaded = progress_tracker["downloaded"]
                    total = progress_tracker["total"]
                    now = time.time()
                    if now - progress_tracker.get("last_report", 0) >= 0.1:
                        progress_tracker["last_report"] = now
                        if total > 0 and progress_callback:
                            pct = min(99, int(downloaded * 100 / total))
                            try:
                                progress_callback(pct, downloaded, total)
                            except Exception:
                                pass
            return True
    except Exception as e:
        logger.warning(f"Chunk download error ({start}-{end}): {e}")
        return False


def _download_single_stream(
    url: str,
    dest_path: str,
    total_size: int,
    progress_callback: Optional[Callable[[int, int, int], None]],
    cancel_event: Optional[threading.Event],
    custom_headers: dict | None = None,
    block_size: int = 65536,
) -> bool:
    """Fallback single-stream sequential download with progress reporting."""
    headers = dict(_BASE_HEADERS)
    if custom_headers:
        headers.update(custom_headers)

    req = urllib.request.Request(url, headers=headers)
    try:
        temp_dest = dest_path + ".tmp"
        with urllib.request.urlopen(req, timeout=30) as res, open(temp_dest, "wb") as f:
            if total_size <= 0:
                total_size = int(res.headers.get("Content-Length", 0))

            downloaded = 0
            last_report = 0
            while True:
                if cancel_event and cancel_event.is_set():
                    return False
                buf = res.read(block_size)
                if not buf:
                    break
                f.write(buf)
                downloaded += len(buf)

                now = time.time()
                if now - last_report >= 0.1:
                    last_report = now
                    if total_size > 0 and progress_callback:
                        pct = min(99, int(downloaded * 100 / total_size))
                        try:
                            progress_callback(pct, downloaded, total_size)
                        except Exception:
                            pass

        if os.path.exists(dest_path):
            try:
                os.remove(dest_path)
            except OSError:
                pass
        os.replace(temp_dest, dest_path)
        if progress_callback:
            progress_callback(100, downloaded, downloaded)
        return True
    except Exception as e:
        logger.warning(f"Single-stream download error: {e}")
        temp_dest = dest_path + ".tmp"
        if os.path.exists(temp_dest):
            try:
                os.remove(temp_dest)
            except OSError:
                pass
        return False


def download_file_parallel(
    url: str,
    dest_path: str,
    progress_callback: Optional[Callable[[int, int, int], None]] = None,
    num_threads: int = 8,
    cancel_event: Optional[threading.Event] = None,
    custom_headers: dict | None = None,
) -> bool:
    """Download a file with multi-threaded chunking (if supported) or single stream fallback.

    Args:
        url: Direct download URL.
        dest_path: Absolute destination path for the saved file.
        progress_callback: Callback receiving (percent, downloaded_bytes, total_bytes).
        num_threads: Number of parallel range download workers (default 8).
        cancel_event: Optional threading.Event to signal cancellation.
        custom_headers: Optional HTTP headers dict.

    Returns:
        True if download completed and verified, False otherwise.
    """
    dest_path_obj = Path(dest_path)
    dest_path_obj.parent.mkdir(parents=True, exist_ok=True)

    # 1. Probe for file size and range capabilities
    total_size, supports_range = _probe_url(url, custom_headers)

    # If byte ranges unsupported or size too small (< 4MB), use single stream
    min_parallel_size = 4 * 1024 * 1024
    if not supports_range or total_size < min_parallel_size:
        return _download_single_stream(
            url,
            dest_path,
            total_size,
            progress_callback,
            cancel_event,
            custom_headers,
        )

    # 2. Pre-allocate the file on disk
    try:
        with open(dest_path, "wb") as f:
            f.truncate(total_size)
    except Exception as e:
        logger.warning(f"Pre-allocation failed ({e}), falling back to single stream")
        return _download_single_stream(
            url,
            dest_path,
            total_size,
            progress_callback,
            cancel_event,
            custom_headers,
        )

    # 3. Calculate chunk ranges
    chunk_size = total_size // num_threads
    ranges: list[tuple[int, int]] = []
    for i in range(num_threads):
        start = i * chunk_size
        end = total_size - 1 if i == num_threads - 1 else (i + 1) * chunk_size - 1
        ranges.append((start, end))

    progress_lock = threading.Lock()
    progress_tracker = {"downloaded": 0, "total": total_size, "last_report": 0}

    # 4. Concurrently download chunks
    success = True
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [
            executor.submit(
                _download_chunk,
                url,
                dest_path,
                start,
                end,
                progress_lock,
                progress_tracker,
                progress_callback,
                cancel_event,
                custom_headers,
            )
            for start, end in ranges
        ]

        for future in as_completed(futures):
            try:
                res = future.result()
                if not res:
                    success = False
            except Exception as e:
                logger.warning(f"Worker thread exception: {e}")
                success = False

    if cancel_event and cancel_event.is_set():
        if os.path.exists(dest_path):
            try:
                os.remove(dest_path)
            except OSError:
                pass
        return False

    if success and os.path.exists(dest_path) and os.path.getsize(dest_path) == total_size:
        if progress_callback:
            progress_callback(100, total_size, total_size)
        return True

    # If parallel failed for some reason, attempt fallback to single stream
    logger.warning("Parallel chunks failed or size mismatch, falling back to single stream")
    return _download_single_stream(
        url,
        dest_path,
        total_size,
        progress_callback,
        cancel_event,
        custom_headers,
    )
