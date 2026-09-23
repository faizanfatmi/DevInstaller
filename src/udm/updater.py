"""Auto-updater logic and background threads for DevInstaller."""

from __future__ import annotations

import json
import re
import sys
import urllib.request
from PySide6.QtCore import QThread, Signal
from udm.logger import logger


def parse_version(v_str: str) -> tuple[int, ...]:
    """Parse version string into a comparable tuple of integers (e.g. 'v1.0.2' -> (1, 0, 2))."""
    v_str = v_str.strip().lower()
    if v_str.startswith("v"):
        v_str = v_str[1:]
    base = re.split(r"[-+]", v_str)[0]
    digits = re.findall(r"\d+", base)
    return tuple(int(x) for x in digits)


def is_newer(latest_version: str, current_version: str) -> bool:
    """Return True if latest_version is newer than current_version."""
    return parse_version(latest_version) > parse_version(current_version)


class UpdateCheckWorker(QThread):
    """Background worker to check for updates on GitHub.

    Signals
    -------
    update_available(dict):
        Emitted if a newer version is available. Passes a dict containing
        latest_version, body (changelog), download_url, asset_name, and html_url.
    no_update_found:
        Emitted if the current version is up-to-date or newer.
    error(str):
        Emitted if the update check fails (e.g. offline, rate limited).
    """

    update_available = Signal(dict)
    no_update_found = Signal()
    error = Signal(str)

    def __init__(self, github_repo: str, current_version: str, parent=None) -> None:
        super().__init__(parent)
        self.github_repo = github_repo
        self.current_version = current_version

    def run(self) -> None:
        try:
            url = f"https://api.github.com/repos/{self.github_repo}/releases/latest"
            req = urllib.request.Request(url, headers={"User-Agent": "devinstaller"})
            
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status != 200:
                    self.error.emit(f"HTTP Error {response.status}")
                    return
                data = json.loads(response.read().decode("utf-8"))

            latest_version = data.get("tag_name", "")
            if not latest_version:
                self.no_update_found.emit()
                return

            if is_newer(latest_version, self.current_version):
                assets = data.get("assets", [])
                download_url = None
                asset_name = None

                # Detect platform extension
                if sys.platform == "win32":
                    ext = ".exe"
                elif sys.platform == "darwin":
                    ext = ".dmg"
                else:
                    ext = ".AppImage"

                # Find matching asset
                for asset in assets:
                    name = asset.get("name", "")
                    if name.endswith(ext):
                        download_url = asset.get("browser_download_url")
                        asset_name = name
                        break

                # Fallback if no matching asset found for the platform
                if not download_url and assets:
                    download_url = assets[0].get("browser_download_url")
                    asset_name = assets[0].get("name")

                release_info = {
                    "latest_version": latest_version,
                    "body": data.get("body", ""),
                    "download_url": download_url,
                    "asset_name": asset_name,
                    "html_url": data.get("html_url", ""),
                }
                self.update_available.emit(release_info)
            else:
                self.no_update_found.emit()

        except Exception as e:
            logger.warning(f"Failed to check for updates: {e}")
            self.error.emit(str(e))


class UpdateDownloadWorker(QThread):
    """Background worker to download the update asset using parallel chunk downloading.

    Signals
    -------
    progress(int):
        Emitted with download percentage (0-100).
    finished(str):
        Emitted with the absolute path of the downloaded file.
    error(str):
        Emitted if the download fails.
    """

    progress = Signal(int)
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, url: str, dest_path: str, parent=None) -> None:
        super().__init__(parent)
        self.url = url
        self.dest_path = dest_path
        import threading
        self._cancel_event = threading.Event()

    def cancel(self) -> None:
        """Signal cancellation cleanly."""
        self._cancel_event.set()

    def run(self) -> None:
        try:
            from udm.downloader import download_file_parallel

            def _on_progress(pct: int, downloaded: int, total: int):
                self.progress.emit(pct)

            success = download_file_parallel(
                url=self.url,
                dest_path=self.dest_path,
                progress_callback=_on_progress,
                num_threads=4,
                cancel_event=self._cancel_event,
            )

            if self._cancel_event.is_set():
                return

            if success:
                self.finished.emit(self.dest_path)
            else:
                self.error.emit("Download failed or was corrupted")
        except Exception as e:
            logger.exception("Failed to download update")
            self.error.emit(str(e))
