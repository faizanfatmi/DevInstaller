"""Unit tests for the parallel chunk downloader."""

import os
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import pytest

from udm.downloader import download_file_parallel, _probe_url, _optimal_thread_count


class RangeTestHandler(BaseHTTPRequestHandler):
    """Test HTTP handler supporting Range requests."""

    data = b"0123456789" * 500000  # 5,000,000 bytes (~5MB)

    def log_message(self, format, *args):
        pass  # Suppress server logs during test

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-Length", str(len(self.data)))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()

    def do_GET(self):
        range_header = self.headers.get("Range")
        if range_header and range_header.startswith("bytes="):
            rng = range_header.split("bytes=")[1]
            parts = rng.split("-")
            start = int(parts[0]) if parts[0] else 0
            end = int(parts[1]) if parts[1] else len(self.data) - 1
            chunk = self.data[start : end + 1]

            self.send_response(206)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Range", f"bytes {start}-{end}/{len(self.data)}")
            self.send_header("Content-Length", str(len(chunk)))
            self.send_header("Accept-Ranges", "bytes")
            self.end_headers()
            self.wfile.write(chunk)
        else:
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(len(self.data)))
            self.send_header("Accept-Ranges", "bytes")
            self.end_headers()
            self.wfile.write(self.data)


@pytest.fixture(scope="module")
def range_server():
    server = HTTPServer(("127.0.0.1", 0), RangeTestHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()


def test_probe_url(range_server):
    total, supports = _probe_url(f"{range_server}/testfile")
    assert total == 5000000
    assert supports is True


def test_download_file_parallel(range_server):
    with tempfile.TemporaryDirectory() as td:
        dest = os.path.join(td, "downloaded.bin")
        progresses = []

        def on_prog(pct, down, tot):
            progresses.append(pct)

        success = download_file_parallel(
            url=f"{range_server}/testfile",
            dest_path=dest,
            progress_callback=on_prog,
            num_threads=4,
        )

        assert success is True
        assert os.path.exists(dest)
        assert os.path.getsize(dest) == 5000000
        assert len(progresses) > 0
        assert progresses[-1] == 100

        with open(dest, "rb") as f:
            downloaded_bytes = f.read()
            assert downloaded_bytes == RangeTestHandler.data


def test_download_cancel(range_server):
    with tempfile.TemporaryDirectory() as td:
        dest = os.path.join(td, "cancelled.bin")
        cancel_evt = threading.Event()
        cancel_evt.set()  # Cancel immediately

        success = download_file_parallel(
            url=f"{range_server}/testfile",
            dest_path=dest,
            cancel_event=cancel_evt,
        )
        assert success is False


class FlakyRangeHandler(BaseHTTPRequestHandler):
    """Range server that truncates the FIRST response for each range once.

    The client should resume the missing tail on retry and assemble a byte-exact
    file — never a size-correct-but-content-corrupt one (the pre-allocation trap).
    """

    data = b"0123456789" * 500000  # 5,000,000 bytes (~5MB)
    _served: dict[str, int] = {}
    _lock = threading.Lock()

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        range_header = self.headers.get("Range", "")
        if range_header.startswith("bytes="):
            rng = range_header.split("bytes=")[1]
            parts = rng.split("-")
            start = int(parts[0]) if parts[0] else 0
            end = int(parts[1]) if parts[1] else len(self.data) - 1
        else:
            start, end = 0, len(self.data) - 1

        full = self.data[start:end + 1]

        key = f"{start}-{end}"
        with self._lock:
            seen = self._served.get(key, 0)
            self._served[key] = seen + 1
        first_time = seen == 0

        # Truncate the tail on the first sizeable request for this exact range.
        body = full[: len(full) // 2] if (first_time and len(full) > 2) else full

        self.send_response(206)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Range", f"bytes {start}-{end}/{len(self.data)}")
        # Advertise the full length but send fewer bytes → simulates a drop.
        self.send_header("Content-Length", str(len(full)))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass


class FlakyStreamHandler(BaseHTTPRequestHandler):
    """No-range server that truncates only its very first response.

    Exercises the single-stream restart path (server ignores Range → 200).
    """

    data = b"abcdefghij" * 200000  # 2,000,000 bytes (~2MB, below parallel cutoff)
    _first = True
    _lock = threading.Lock()

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        with self._lock:
            truncate = FlakyStreamHandler._first
            FlakyStreamHandler._first = False
        body = self.data[: len(self.data) // 2] if truncate else self.data

        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Length", str(len(self.data)))
        # Deliberately no Accept-Ranges → forces the single-stream path.
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass


@pytest.fixture
def flaky_range_server():
    FlakyRangeHandler._served = {}
    server = HTTPServer(("127.0.0.1", 0), FlakyRangeHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()


@pytest.fixture
def flaky_stream_server():
    FlakyStreamHandler._first = True
    server = HTTPServer(("127.0.0.1", 0), FlakyStreamHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()


def test_parallel_resumes_after_truncation(flaky_range_server):
    """A truncated chunk must resume and produce a byte-exact file, not corruption."""
    with tempfile.TemporaryDirectory() as td:
        dest = os.path.join(td, "resumed.bin")
        success = download_file_parallel(
            url=f"{flaky_range_server}/testfile",
            dest_path=dest,
            num_threads=4,
        )
        assert success is True
        assert os.path.getsize(dest) == len(FlakyRangeHandler.data)
        with open(dest, "rb") as f:
            assert f.read() == FlakyRangeHandler.data


def test_single_stream_restarts_after_drop(flaky_stream_server):
    """A dropped single-stream download restarts and completes byte-exact."""
    with tempfile.TemporaryDirectory() as td:
        dest = os.path.join(td, "stream.bin")
        success = download_file_parallel(
            url=f"{flaky_stream_server}/testfile",
            dest_path=dest,
        )
        assert success is True
        assert os.path.getsize(dest) == len(FlakyStreamHandler.data)
        with open(dest, "rb") as f:
            assert f.read() == FlakyStreamHandler.data


def test_optimal_thread_count_scaling():
    """Worker count honours the caller as a floor and scales up for big files."""
    kb, mb, gb = 1024, 1024 * 1024, 1024 * 1024 * 1024
    # Small file: caller's request respected, not inflated.
    assert _optimal_thread_count(2 * mb, 4) == 4
    # Mid file lifts a low request up to the size tier.
    assert _optimal_thread_count(64 * mb, 2) == 8
    # Large file scales to the ceiling regardless of a modest request.
    assert _optimal_thread_count(2 * gb, 8) == 16
    # Ceiling is never exceeded.
    assert _optimal_thread_count(2 * gb, 64) == 16
    # Never returns zero for a tiny/zero size.
    assert _optimal_thread_count(0, 1) >= 1
