"""Unit tests for the parallel chunk downloader."""

import os
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import pytest

from udm.downloader import download_file_parallel, _probe_url


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
