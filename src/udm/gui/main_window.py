"""Main application window — assembles all GUI sections with sidebar layout."""

import os
import sys
import threading

from PySide6.QtCore import QObject, Qt, Signal, Slot, QTimer
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from udm.config import get_categories, load_tools
from udm.constants import (
    MIN_HEIGHT,
    MIN_WIDTH,
    WINDOW_HEIGHT,
    WINDOW_TITLE,
    WINDOW_WIDTH,
)
from udm.gui.action_bar import ActionBar
from udm.gui.header import HeaderBar
from udm.gui.log_panel import LogPanel
from udm.gui.search_bar import SearchBar
from udm.gui.sidebar import Sidebar
from udm.gui.status_bar import StatusBar
from udm.gui.theme import BG_WINDOW, build_stylesheet
from udm.gui.tool_table import ToolTable
from udm.installer import install_selected, set_log_callback, set_progress_callback
from udm.logger import logger
from udm.network import check_internet


class WorkerSignals(QObject):
    """Signals for cross-thread communication."""

    progress = Signal(str, str, int)
    log_message = Signal(str)
    finished = Signal(dict)


class MainWindow(QMainWindow):
    """Primary application window with sidebar layout."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setMinimumSize(MIN_WIDTH, MIN_HEIGHT)
        self.setStyleSheet(build_stylesheet())
        self._apply_window_icon()

        self._installing = False
        self._version_worker = None
        self._signals = WorkerSignals()
        self._signals.progress.connect(self._on_progress)
        self._signals.log_message.connect(self._on_log)
        self._signals.finished.connect(self._on_install_finished)

        self._all_tools = load_tools()
        self._categories = get_categories(self._all_tools)
        self._tool_counts = self._compute_tool_counts()

        self._build_ui()
        self._connect_signals()
        self._setup_callbacks()
        self._center_on_screen()

        # Non-blocking automatic check for updates 1 second after startup
        QTimer.singleShot(1000, self._check_for_updates)

    def showEvent(self, event):
        """Apply the Windows 11 Mica backdrop once the native window exists."""
        super().showEvent(event)
        if not getattr(self, "_backdrop_applied", False):
            self._backdrop_applied = True
            try:
                from udm.gui.mica import apply_backdrop

                apply_backdrop(self)
            except Exception:
                pass  # cosmetic only

    def _apply_window_icon(self):
        """Set the window icon from the bundled logo.png, if present."""
        from PySide6.QtGui import QIcon

        from udm.config import resource_path
        from udm.constants import LOGO_FILENAME

        logo = resource_path(LOGO_FILENAME)
        if logo.exists():
            self.setWindowIcon(QIcon(str(logo)))

    def _compute_tool_counts(self) -> dict[str, int]:
        """Compute tool count per category."""
        counts: dict[str, int] = {}
        for tool in self._all_tools:
            cat = tool.get("category", "Other")
            counts[cat] = counts.get(cat, 0) + 1
        return counts

    def _center_on_screen(self):
        screen = self.screen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def _build_ui(self):
        central = QWidget()
        central.setStyleSheet(f"background-color: {BG_WINDOW};")
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Header (full width)
        self.header = HeaderBar()
        root_layout.addWidget(self.header)

        # Main content area: sidebar + content
        content_area = QWidget()
        content_layout = QHBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Sidebar
        self.sidebar = Sidebar(self._categories, self._tool_counts)
        content_layout.addWidget(self.sidebar)

        # Right content panel
        right_panel = QWidget()
        right_panel.setStyleSheet(f"background-color: {BG_WINDOW};")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # Search bar
        self.search_bar = SearchBar(self._categories)
        self.search_bar.set_tools(self._all_tools)
        right_layout.addWidget(self.search_bar)

        # Tool table
        self.tool_table = ToolTable(self._all_tools)
        right_layout.addWidget(self.tool_table, stretch=1)

        # Log panel
        self.log_panel = LogPanel()
        right_layout.addWidget(self.log_panel)

        # Action bar
        self.action_bar = ActionBar()
        right_layout.addWidget(self.action_bar)

        content_layout.addWidget(right_panel, stretch=1)
        root_layout.addWidget(content_area, stretch=1)

        # Status bar (full width)
        self.status_bar = StatusBar()
        root_layout.addWidget(self.status_bar)

    def _connect_signals(self):
        self.search_bar.filter_changed.connect(self._apply_filter)
        self.search_bar.refresh_requested.connect(self._on_refresh)
        self.search_bar.ai_select_requested.connect(self._on_ai_select)
        self.search_bar.ai_clear_requested.connect(self._on_ai_clear)
        self.sidebar.category_selected.connect(self._on_category_selected)
        self.tool_table.selection_changed.connect(self._on_selection_changed)
        self.action_bar.clear_clicked.connect(self._on_clear)
        self.action_bar.install_clicked.connect(self._on_install)

    def _setup_callbacks(self):
        set_progress_callback(
            lambda tool, status, pct: self._signals.progress.emit(tool, status, pct)
        )
        set_log_callback(lambda msg: self._signals.log_message.emit(msg))

    def _on_category_selected(self, category: str):
        """Handle sidebar category selection."""
        self.search_bar.set_category(category)

    def _apply_filter(self):
        query = self.search_bar.search_text()
        category = self.search_bar.selected_category()
        self.tool_table.apply_filter(query, category)

    def _on_selection_changed(self, count: int):
        self.action_bar.update_state(count)

    def _on_clear(self):
        self.tool_table.clear_selection()

    def _on_ai_select(self, keys: list):
        """Handle AI Stack parse results — select matching tools."""
        self.tool_table.select_tools_by_keys(keys)
        count = len(keys)
        names = ", ".join(keys[:6])
        if count > 6:
            names += f" +{count - 6} more"
        self.log_panel.append_log(f"🔍  AI Stack detected {count} tools: {names}")
        self.status_bar.set_status_text(f"AI Stack — {count} tools selected")

    def _on_ai_clear(self):
        """Handle clearing of AI Stack results."""
        self.tool_table.clear_selection()
        self._apply_filter()
        self.status_bar.set_status_text("Ready")

    def _on_refresh(self):
        self._all_tools = load_tools()
        self._categories = get_categories(self._all_tools)
        self._tool_counts = self._compute_tool_counts()
        self.search_bar.set_categories(self._categories)
        self.search_bar.set_tools(self._all_tools)
        self.tool_table.rebuild(self._all_tools)
        self._apply_filter()
        self.log_panel.append_log("↻  Tool list refreshed from tools.json")
        self._maybe_refresh_versions()

    def _maybe_refresh_versions(self):
        """Kick off an optional, non-blocking Gemini version refresh.

        Does nothing when the Gemini API key is not configured, so default
        behaviour is unchanged for users without AI enabled.
        """
        from udm.ai import gemini_available

        if not gemini_available():
            return
        if getattr(self, "_version_worker", None) is not None:
            return  # a refresh is already running

        from udm.ai.worker import VersionRefreshWorker

        names = sorted({t.get("name", "") for t in self._all_tools if t.get("name")})
        if not names:
            return

        self.log_panel.append_log("🤖  Checking latest language/compiler versions…")
        worker = VersionRefreshWorker(names)
        worker.finished_versions.connect(self._on_versions_ready)
        worker.failed.connect(self._on_versions_failed)
        worker.finished.connect(self._clear_version_worker)
        self._version_worker = worker
        worker.start()

    @Slot(dict)
    def _on_versions_ready(self, versions: dict):
        if not versions:
            return
        for tool in self._all_tools:
            latest = versions.get(tool.get("name", ""))
            if latest:
                tool["latest_version"] = latest
        self.log_panel.append_log(
            f"✓  Updated version info for {len(versions)} item(s)."
        )
        self.status_bar.set_status_text("Version metadata updated")

    @Slot(str)
    def _on_versions_failed(self, message: str):
        self.log_panel.append_log(f"⚠  Version check skipped: {message}")

    def _clear_version_worker(self):
        self._version_worker = None

    def _check_for_updates(self):
        """Kick off a non-blocking background check for app updates from GitHub."""
        from udm.constants import APP_VERSION
        from udm.updater import UpdateCheckWorker

        github_repo = os.environ.get("DEVINSTALLER_GITHUB_REPO", "faizanfatmi/DevInstaller").strip()

        self.log_panel.append_log("🔍  Checking for software updates...")
        self._update_worker = UpdateCheckWorker(github_repo, APP_VERSION, self)
        self._update_worker.update_available.connect(self._on_update_available)
        self._update_worker.no_update_found.connect(
            lambda: self.log_panel.append_log("✓  DevInstaller is up to date.")
        )
        self._update_worker.error.connect(
            lambda err: self.log_panel.append_log(f"⚠  Update check failed: {err}")
        )
        self._update_worker.finished.connect(self._clear_update_worker)
        self._update_worker.start()

    @Slot(dict)
    def _on_update_available(self, release_info: dict):
        """Display the update dialog when a new version is detected."""
        from udm.constants import APP_VERSION
        from udm.gui.update_dialog import UpdateDialog

        self.log_panel.append_log(f"✨  New update available: {release_info['latest_version']}!")

        # Construct and execute the premium update dialog modal
        dialog = UpdateDialog(release_info, APP_VERSION, self)
        dialog.exec()

    def _clear_update_worker(self):
        self._update_worker = None

    def _on_install(self):
        tools = self.tool_table.selected_tools()
        if not tools:
            QMessageBox.warning(
                self, "Nothing selected", "Select at least one tool first."
            )
            return
        if self._installing:
            QMessageBox.information(self, "Busy", "An installation is already running.")
            return

        self.log_panel.append_log("Checking internet connection…")
        if not check_internet():
            QMessageBox.critical(
                self, "No Internet", "Please connect to the internet and try again."
            )
            self.log_panel.append_log("✗ No internet — aborted.")
            return

        self._installing = True
        self.status_bar.set_progress(0)
        self.status_bar.set_status_text("Starting installation…")

        names = ", ".join(t["name"] for t in tools)
        self.log_panel.append_log(f"Selected: {names}")

        def worker():
            try:
                results = install_selected(tools)
            except Exception as ex:
                logger.exception("Unhandled error during installation")
                results = {}
            finally:
                self._installing = False
                self._signals.finished.emit(results)

        threading.Thread(target=worker, daemon=True).start()

    @Slot(str, str, int)
    def _on_progress(self, tool: str, status: str, pct: int):
        self.status_bar.set_progress(pct)
        self.status_bar.set_status_text(f"{tool}  ·  {status}")

    @Slot(str)
    def _on_log(self, msg: str):
        self.log_panel.append_log(msg)

    @Slot(dict)
    def _on_install_finished(self, results: dict):
        self.status_bar.set_progress(100)

        installed = sum(1 for v in results.values() if v == "installed")
        skipped = sum(1 for v in results.values() if v == "already_installed")
        failed = sum(1 for v in results.values() if v == "failed")
        failed_names = [k for k, v in results.items() if v == "failed"]

        if failed:
            self.status_bar.set_status_text("Completed with errors")
        else:
            self.status_bar.set_status_text("All done — happy coding! 🎉")

        from udm.gui.completion_dialog import CompletionDialog

        dialog = CompletionDialog(
            installed=installed,
            skipped=skipped,
            failed=failed,
            failed_names=failed_names,
            parent=self,
        )
        dialog.exec()

    def closeEvent(self, event):
        if self._installing:
            reply = QMessageBox.question(
                self,
                "Confirm",
                "Installation in progress. Force exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
        event.accept()
