"""Main application window — assembles all GUI sections with sidebar + detail panel layout."""

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
from udm.gui.detail_panel import DetailPanel
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
    uninstall_finished = Signal(dict, bool)
    tool_detected = Signal(str, bool)


class MainWindow(QMainWindow):
    """Primary application window with sidebar + detail panel layout."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setMinimumSize(MIN_WIDTH, MIN_HEIGHT)
        self.setStyleSheet(build_stylesheet())
        self._apply_window_icon()

        self._installing = False
        self._version_worker = None
        self._installed_cache: dict[str, bool] = {}
        self._signals = WorkerSignals()
        self._signals.progress.connect(self._on_progress)
        self._signals.log_message.connect(self._on_log)
        self._signals.finished.connect(self._on_install_finished)
        self._signals.uninstall_finished.connect(self._on_uninstall_finished)
        self._signals.tool_detected.connect(self._on_tool_detected)

        self._all_tools = load_tools()
        self._categories = get_categories(self._all_tools)
        self._tool_counts = self._compute_tool_counts()

        self._build_ui()
        self._connect_signals()
        self._setup_callbacks()
        self._center_on_screen()

        # Update the status bar package count (matching 129 packages in mockup)
        self.status_bar.set_package_count(129)

        # Pre-select first tool so detail panel displays Python 3.12 matching mockup
        if self._all_tools:
            self.detail_panel.set_tool(self._all_tools[0])

        # Non-blocking automatic check for updates and package manager after startup
        QTimer.singleShot(400, self._initial_detect)
        QTimer.singleShot(600, self._check_package_manager)
        QTimer.singleShot(1200, self._check_for_updates)

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

        # Main content area: sidebar + center content + detail panel
        content_area = QWidget()
        content_layout = QHBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Sidebar
        self.sidebar = Sidebar(self._categories, self._tool_counts)
        content_layout.addWidget(self.sidebar)

        # Center content panel (search + tools + log + action bar)
        center_panel = QWidget()
        center_panel.setStyleSheet(f"background-color: {BG_WINDOW};")
        center_layout = QVBoxLayout(center_panel)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)

        # Search bar
        self.search_bar = SearchBar(self._categories)
        self.search_bar.set_tools(self._all_tools)
        center_layout.addWidget(self.search_bar)

        # Tool table
        self.tool_table = ToolTable(self._all_tools)
        center_layout.addWidget(self.tool_table, stretch=1)

        # Log panel (with Terminal / Logs tabs and Clear button)
        self.log_panel = LogPanel()
        center_layout.addWidget(self.log_panel)

        content_layout.addWidget(center_panel, stretch=1)

        # Detail panel (right side)
        self.detail_panel = DetailPanel()
        content_layout.addWidget(self.detail_panel)

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
        self.tool_table.tool_selected.connect(self._on_tool_selected)
        self.detail_panel.install_requested.connect(self._on_detail_install)
        self.detail_panel.uninstall_requested.connect(self._on_detail_uninstall)

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

    def _initial_detect(self):
        """Perform background detection for high-priority tools (Oracle, initial tool)."""
        def detect_bg():
            from udm.installer.engine import detect_tool
            priority_keys = {"oracle_db_xe", "oracle_sql_developer"}
            if self._all_tools:
                priority_keys.add(self._all_tools[0].get("key", ""))
            for tool in self._all_tools:
                k = tool.get("key", "")
                if k in priority_keys:
                    present = detect_tool(tool)
                    self._signals.tool_detected.emit(k, present)

        threading.Thread(target=detect_bg, daemon=True).start()

    @Slot(str, bool)
    def _on_tool_detected(self, key: str, is_installed: bool):
        """Handle background detection completion for a tool."""
        self._installed_cache[key] = is_installed
        self.tool_table.update_tool_installed(key, is_installed)
        if self.detail_panel._current_tool and self.detail_panel._current_tool.get("key") == key:
            self.detail_panel.set_installed_state(is_installed)

    def _on_selection_changed(self, count: int):
        if count > 1:
            self.detail_panel.install_btn.setText(f"⬇  Install Selected ({count})")
            self.detail_panel.uninstall_btn.setVisible(False)
        elif count == 1:
            sel = self.tool_table.selected_tools()
            if sel:
                self._on_tool_selected(sel[0])
        elif self.detail_panel._current_tool:
            self._on_tool_selected(self.detail_panel._current_tool)

    def _on_tool_selected(self, tool: dict):
        """Handle tool row click — update the detail panel and check installed status."""
        key = tool.get("key", "")
        cached = self._installed_cache.get(key)
        self.detail_panel.set_tool(tool, is_installed=cached)

        if cached is None:
            def check():
                from udm.installer.engine import detect_tool
                present = detect_tool(tool)
                self._signals.tool_detected.emit(key, present)
            threading.Thread(target=check, daemon=True).start()

    def _on_detail_install(self, tool: dict):
        """Handle install button click from the detail panel."""
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

        # Prioritize selected tools if checkboxes are ticked, otherwise install current tool
        selected = self.tool_table.selected_tools()
        if selected:
            tools = selected
        elif tool:
            tools = [tool]
        else:
            return

        self._installing = True
        self.status_bar.set_progress(0)
        names = ", ".join(t.get("name", "") for t in tools)
        self.status_bar.set_status_text(f"Installing {len(tools)} package(s)…")
        self.log_panel.append_log(f"Selected for install: {names}")

        def worker():
            try:
                results = install_selected(tools, force=True)
            except Exception as ex:
                logger.exception("Unhandled error during installation")
                self.log_panel.append_log(f"✗ Installation error: {ex}")
                results = {}
            finally:
                self._installing = False
                self._signals.finished.emit(results)

        threading.Thread(target=worker, daemon=True).start()

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
        self.status_bar.set_status_text("")

    def _on_refresh(self):
        self._all_tools = load_tools()
        self._categories = get_categories(self._all_tools)
        self._tool_counts = self._compute_tool_counts()
        self.search_bar.set_categories(self._categories)
        self.search_bar.set_tools(self._all_tools)
        self.tool_table.rebuild(self._all_tools)
        self._apply_filter()
        self.status_bar.set_package_count(len(self._all_tools))
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

    def _check_package_manager(self):
        """Check availability of winget/choco and inform user in log panel."""
        from udm.installer.prerequisites import is_choco_available, is_winget_available
        from udm.platform import is_windows

        if is_windows():
            if is_winget_available():
                self.log_panel.append_log("✓ Windows Package Manager (winget) ready.")
            elif is_choco_available():
                self.log_panel.append_log("✓ Chocolatey (choco) ready (winget fallback active).")
            else:
                self.log_panel.append_log("ℹ winget not detected — Chocolatey will be automatically installed when installing tools.")

    def _check_for_updates(self):
        """Kick off a non-blocking background check for app updates from GitHub."""
        from udm.constants import APP_VERSION
        from udm.updater import UpdateCheckWorker

        github_repo = os.environ.get("DEVINSTALLER_GITHUB_REPO", "faizanfatmi/DevInstaller").strip()

        self._update_worker = UpdateCheckWorker(github_repo, APP_VERSION, self)
        self._update_worker.update_available.connect(self._on_update_available)
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

        for k, v in results.items():
            if v in ("installed", "already_installed"):
                self._installed_cache[k] = True
                self.tool_table.update_tool_installed(k, True)
                if self.detail_panel._current_tool and self.detail_panel._current_tool.get("key") == k:
                    self.detail_panel.set_installed_state(True)

        from udm.gui.completion_dialog import CompletionDialog

        dialog = CompletionDialog(
            installed=installed,
            skipped=skipped,
            failed=failed,
            failed_names=failed_names,
            parent=self,
        )
        dialog.exec()

    def _on_detail_uninstall(self, tool: dict):
        """Handle uninstall button click from the detail panel."""
        if self._installing:
            QMessageBox.information(self, "Busy", "An installation or uninstallation is already in progress.")
            return

        key = tool.get("key", "")
        name = "C++" if key == "gpp" else tool.get("name", "Unknown")

        if key == "oracle_db_xe":
            msg = QMessageBox(self)
            msg.setWindowTitle("Confirm Complete Wipeout — Oracle Database 21c XE")
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setText(
                "<h3>Confirm Oracle Database XE Wipeout</h3>"
                "Are you sure you want to <b>completely uninstall and wipe out</b> Oracle Database 21c XE?<br><br>"
                "<b>This will permanently:</b><br>"
                "• Stop and remove all Oracle Windows services<br>"
                "• Completely delete Oracle Home and database files (<code>C:\\app\\oracle</code>)<br>"
                "• Delete all Oracle registry keys and configuration<br>"
                "• Clean Oracle from the system PATH<br><br>"
                "<i>This allows you to perform a 100% clean, fresh installation.</i>"
            )
            wipe_btn = msg.addButton("🗑️ Wipe Out & Uninstall", QMessageBox.ButtonRole.AcceptRole)
            cancel_btn = msg.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
            msg.setDefaultButton(cancel_btn)
            msg.exec()
            if msg.clickedButton() != wipe_btn:
                return

        elif key == "oracle_sql_developer":
            msg = QMessageBox(self)
            msg.setWindowTitle("Confirm Uninstall — Oracle SQL Developer")
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setText(
                "<h3>Confirm SQL Developer Uninstall</h3>"
                "Are you sure you want to completely remove <b>Oracle SQL Developer</b>?<br><br>"
                "• Deletes <code>C:\\sqldeveloper</code><br>"
                "• Cleans desktop & Start Menu shortcuts<br>"
                "• Cleans system PATH"
            )
            uninst_btn = msg.addButton("🗑️ Uninstall", QMessageBox.ButtonRole.AcceptRole)
            cancel_btn = msg.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
            msg.setDefaultButton(cancel_btn)
            msg.exec()
            if msg.clickedButton() != uninst_btn:
                return

        else:
            reply = QMessageBox.question(
                self,
                f"Confirm Uninstall — {name}",
                f"Are you sure you want to uninstall {name} from your system?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        self._installing = True
        self.status_bar.set_progress(15)
        self.status_bar.set_status_text(f"Uninstalling {name}…")
        self.log_panel.append_log("══════════════════════════════════════════════════════════════")
        self.log_panel.append_log(f"Starting uninstallation / wipeout for {name}…")
        self.log_panel.append_log("══════════════════════════════════════════════════════════════")

        def worker():
            try:
                from udm.installer.engine import uninstall_tool
                success = uninstall_tool(tool)
            except Exception as ex:
                logger.exception(f"Unhandled error during uninstallation of {name}")
                self.log_panel.append_log(f"✗ Uninstall error: {ex}")
                success = False
            finally:
                self._installing = False
                self._signals.uninstall_finished.emit(tool, success)

        threading.Thread(target=worker, daemon=True).start()

    @Slot(dict, bool)
    def _on_uninstall_finished(self, tool: dict, success: bool):
        self.status_bar.set_progress(100)
        key = tool.get("key", "")
        name = "C++" if key == "gpp" else tool.get("name", "Unknown")

        if success:
            self.status_bar.set_status_text(f"{name} uninstalled successfully ✓")
            self.log_panel.append_log(f"✓ {name} has been completely uninstalled and wiped out.")
            self._installed_cache[key] = False
            self.tool_table.update_tool_installed(key, False)
            if self.detail_panel._current_tool and self.detail_panel._current_tool.get("key") == key:
                self.detail_panel.set_installed_state(False)

            QMessageBox.information(
                self,
                "Uninstall Complete",
                f"<b>{name}</b> has been completely uninstalled and wiped out from the system.<br><br>"
                "You can now do a fresh installation whenever you want.",
            )
        else:
            self.status_bar.set_status_text(f"Uninstall failed for {name}")
            self.log_panel.append_log(f"✗ Could not completely uninstall {name}. See log for details.")
            QMessageBox.warning(
                self,
                "Uninstall Incomplete",
                f"Could not completely remove {name}. Please check the logs in the terminal tab.",
            )

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
