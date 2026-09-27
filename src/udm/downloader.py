"""High-performance parallel chunk downloader for DevInstaller.

Features:
- Multi-threaded byte-range chunk download (HTTP 206 Partial Content).
- Non-blocking pre-allocated file streaming with thread-isolated file pointers.
- Per-chunk resume + retry: a dropped connection re-requests only the bytes that
  are still missing instead of discarding the whole (possibly multi-GB) download.
- Adaptive worker count that scales with file size to saturate per-connection
  throttled CDNs (GitHub / Oracle) without hammering small files.
- Live progress reporting (percentage, downloaded bytes, total bytes).
- Graceful fallback to single-stream download (also retried) when byte ranges
  are unsupported.
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

# 1 MiB read buffer — fewer syscalls and less progress-lock contention per byte
# than the old 128 KiB, which measurably speeds up high-bandwidth transfers.
_CHUNK_BLOCK_SIZE = 1024 * 1024
_STREAM_BLOCK_SIZE = 512 * 1024

# Hard ceiling on parallel connections. More than this rarely helps and risks
# tripping per-client connection limits / throttling on the origin.
_MAX_THREADS = 16

# Files below this size download as a single stream: the range-probe round-trip
# plus per-thread setup costs more than it saves for small assets.
_MIN_PARALLEL_SIZE = 4 * 1024 * 1024

# Consecutive stalls (a connection making zero progress) tolerated per chunk /
# per single stream before giving up. Progress resets the counter, so a long
# transfer with occasional blips keeps going indefinitely.
_MAX_STALLS = 5


def _size_tier(total_size: int) -> int:
    """Suggest a worker count for *total_size* bytes.

    CDNs commonly throttle each connection, so opening more connections is the
    dominant speed lever for large files — but tiny files gain nothing from a
    crowd of threads, so scale gently.
    """
    mb = total_size / (1024 * 1024)
    if mb < 16:
        return 4
    if mb < 128:
        return 8
    if mb < 512:
        return 12
    return _MAX_THREADS


def _optimal_thread_count(total_size: int, requested: int) -> int:
    """Blend the caller's requested worker count with a size-based suggestion.

    The caller's value acts as a floor (so existing callers never lose threads),
    the size tier can raise it for big files, and everything is capped at
    ``_MAX_THREADS``.
    """
    requested = max(1, requested)
    return max(1, min(_MAX_THREADS, max(requested, _size_tier(total_size))))


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


def _report_progress(
    progress_lock: threading.Lock,
    progress_tracker: dict,
    new_bytes: int,
    progress_callback: Optional[Callable[[int, int, int], None]],
) -> None:
    """Add *new_bytes* to the shared tracker and emit throttled progress.

    Only newly written bytes are counted, so resumed/retried ranges never
    double-count toward the percentage.
    """
    with progress_lock:
        progress_tracker["downloaded"] += new_bytes
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
    block_size: int = _CHUNK_BLOCK_SIZE,
) -> bool:
    """Download the byte range [start, end] into the pre-allocated file.

    Resumes across dropped/truncated connections: each retry re-requests only
    the bytes not yet written, and the stall counter resets whenever any forward
    progress is made. Returns True only when every byte in the range is written,
    so a short read can never be mistaken for a completed chunk.
    """
    pos = start  # next absolute byte offset still needed
    stalls = 0

    while pos <= end:
        if cancel_event and cancel_event.is_set():
            return False

        before = pos
        headers = {**_BASE_HEADERS, "Range": f"bytes={pos}-{end}"}
        if custom_headers:
            headers.update(custom_headers)
        req = urllib.request.Request(url, headers=headers)

        try:
            with urllib.request.urlopen(req, timeout=30) as res, open(dest_path, "r+b") as f:
                f.seek(pos)
                while pos <= end:
                    if cancel_event and cancel_event.is_set():
                        return False
                    to_read = min(block_size, end - pos + 1)
                    buf = res.read(to_read)
                    if not buf:
                        break  # server closed early; retry the remaining range
                    f.write(buf)
                    n = len(buf)
                    pos += n
                    _report_progress(progress_lock, progress_tracker, n, progress_callback)
        except Exception as e:
            logger.debug(f"Chunk stream interrupted ({pos}-{end}): {e}")

        if pos > end:
            return True

        if pos > before:
            stalls = 0  # made progress this attempt — keep going patiently
        else:
            stalls += 1
            if stalls > _MAX_STALLS:
                logger.warning(f"Chunk download gave up after {stalls} stalls ({start}-{end}).")
                return False
        time.sleep(min(0.25 * (2 ** stalls), 4.0))

    return True


def _download_single_stream(
    url: str,
    dest_path: str,
    total_size: int,
    progress_callback: Optional[Callable[[int, int, int], None]],
    cancel_event: Optional[threading.Event],
    custom_headers: dict | None = None,
    block_size: int = _STREAM_BLOCK_SIZE,
) -> bool:
    """Fallback sequential download, resumed on transient failures.

    Used for servers without byte-range support and for small files. When the
    origin honours ranges we resume from the partial ``.tmp`` file; otherwise we
    restart it. Progress is reported against the running total.
    """
    temp_dest = dest_path + ".tmp"
    downloaded = 0
    stalls = 0

    def _remove_temp() -> None:
        if os.path.exists(temp_dest):
            try:
                os.remove(temp_dest)
            except OSError:
                pass

    _remove_temp()

    while True:
        if cancel_event and cancel_event.is_set():
            _remove_temp()
            return False

        before = downloaded
        headers = dict(_BASE_HEADERS)
        if custom_headers:
            headers.update(custom_headers)

        # Resume from what we already have when the server supports it.
        resume = downloaded > 0
        if resume:
            headers["Range"] = f"bytes={downloaded}-"
        open_mode = "ab" if resume else "wb"

        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as res:
                # If we asked to resume but the server ignored ranges (200 not
                # 206), it will resend from byte 0 — restart cleanly instead of
                # appending duplicate bytes.
                if resume and getattr(res, "status", 200) != 206:
                    _remove_temp()
                    downloaded = 0
                    open_mode = "wb"

                if total_size <= 0:
                    hdr_len = int(res.headers.get("Content-Length", 0))
                    if hdr_len and open_mode == "wb":
                        total_size = hdr_len

                with open(temp_dest, open_mode) as f:
                    while True:
                        if cancel_event and cancel_event.is_set():
                            _remove_temp()
                            return False
                        buf = res.read(block_size)
                        if not buf:
                            break
                        f.write(buf)
                        downloaded += len(buf)
                        _report_progress_stream(
                            downloaded, total_size, progress_callback
                        )
        except Exception as e:
            logger.debug(f"Single-stream interrupted at {downloaded} bytes: {e}")

        # Success: either we know the size and matched it, or the stream ended
        # cleanly with no known size but forward progress was made.
        done = (total_size > 0 and downloaded >= total_size) or (
            total_size <= 0 and downloaded > 0 and downloaded == before
        )
        if done:
            break

        if downloaded > before:
            stalls = 0
        else:
            stalls += 1
            if stalls > _MAX_STALLS:
                logger.warning("Single-stream download gave up after repeated stalls.")
                _remove_temp()
                return False
        time.sleep(min(0.25 * (2 ** stalls), 4.0))

    try:
        if os.path.exists(dest_path):
            try:
                os.remove(dest_path)
            except OSError:
                pass
        os.replace(temp_dest, dest_path)
    except OSError as e:
        logger.warning(f"Could not finalize download: {e}")
        _remove_temp()
        return False

    if progress_callback:
        progress_callback(100, downloaded, downloaded)
    return True


def _report_progress_stream(
    downloaded: int,
    total_size: int,
    progress_callback: Optional[Callable[[int, int, int], None]],
) -> None:
    """Throttled progress emit for the single-stream path (no shared lock)."""
    now = time.time()
    last = getattr(_report_progress_stream, "_last", 0.0)
    if now - last < 0.1:
        return
    _report_progress_stream._last = now  # type: ignore[attr-defined]
    if total_size > 0 and progress_callback:
        pct = min(99, int(downloaded * 100 / total_size))
        try:
            progress_callback(pct, downloaded, total_size)
        except Exception:
            pass


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
        num_threads: Baseline parallel range workers. Treated as a floor; the
            downloader may open more (up to 16) for large files, or fewer for
            small ones.
        cancel_event: Optional threading.Event to signal cancellation.
        custom_headers: Optional HTTP headers dict.

    Returns:
        True if download completed and verified, False otherwise.
    """
    dest_path_obj = Path(dest_path)
    dest_path_obj.parent.mkdir(parents=True, exist_ok=True)

    # 1. Probe for file size and range capabilities
    total_size, supports_range = _probe_url(url, custom_headers)

    # If byte ranges unsupported or size too small, use single stream.
    if not supports_range or total_size < _MIN_PARALLEL_SIZE:
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

    # 3. Pick a worker count that suits the file size, then split into ranges.
    workers = _optimal_thread_count(total_size, num_threads)
    chunk_size = total_size // workers
    ranges: list[tuple[int, int]] = []
    for i in range(workers):
        start = i * chunk_size
        end = total_size - 1 if i == workers - 1 else (i + 1) * chunk_size - 1
        ranges.append((start, end))

    progress_lock = threading.Lock()
    progress_tracker = {"downloaded": 0, "total": total_size, "last_report": 0}

    # 4. Concurrently download chunks (each retries/resumes independently).
    success = True
    with ThreadPoolExecutor(max_workers=workers) as executor:
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
                if not future.result():
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

    # If parallel failed for some reason, attempt fallback to single stream.
    logger.warning("Parallel chunks failed or size mismatch, falling back to single stream")
    return _download_single_stream(
        url,
        dest_path,
        total_size,
        progress_callback,
        cancel_event,
        custom_headers,
    )
