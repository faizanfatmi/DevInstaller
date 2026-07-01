"""Qt worker that runs version refresh off the UI thread.

Keeping the network round-trip on a background :class:`QThread` ensures the
Gemini call never freezes the interface. Results are delivered back to the main
thread via signals.
"""

from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from udm.ai.version_updater import VersionUpdater
from udm.logger import logger


class VersionRefreshWorker(QThread):
    """Background worker that refreshes language versions.

    Signals
    -------
    finished_versions(dict):
        Emitted with the resulting ``{name: version}`` mapping on success or
        with the cached mapping on failure. Always emitted exactly once.
    failed(str):
        Emitted with a human-readable message if the refresh produced no data.
    """

    finished_versions = Signal(dict)
    failed = Signal(str)

    def __init__(self, names: list[str], force: bool = False, parent=None) -> None:
        super().__init__(parent)
        self._names = list(names)
        self._force = force
        self._updater = VersionUpdater()

    def run(self) -> None:  # noqa: D401 - QThread entry point
        try:
            versions = self._updater.refresh(self._names, force=self._force)
        except Exception as e:  # noqa: BLE001 - worker must not crash the app
            logger.exception(f"Version refresh worker crashed: {e}")
            self.failed.emit(str(e))
            self.finished_versions.emit({})
            return

        if not versions:
            self.failed.emit("No version data available.")
        self.finished_versions.emit(versions)
