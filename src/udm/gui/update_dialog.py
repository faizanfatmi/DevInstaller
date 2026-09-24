"""Premium Software Update dialog — monochrome dark theme.

Prompts the user with new release information, shows release notes,
and performs a background download and self-update execution.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from udm.gui.theme import (
    AMBER,
    BG_CARD,
    BG_INPUT,
    BG_LOG,
    BG_ROW_HOVER,
    BG_WINDOW,
    BORDER,
    BORDER_ACCENT,
    BORDER_LIGHT,
    FG,
    FG_DIM,
    FG_MUTED,
    GREEN,
    GREEN_DIM,
)
from udm.gui.widgets import ActionButton, PillBadge
from udm.updater import UpdateDownloadWorker


class UpdateDialog(QDialog):
    """Modern software update dialog with inline download progress and self-updating execution."""

    def __init__(self, release_info: dict, current_version: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Software Update")
        self.setModal(True)
        self.setMinimumSize(520, 460)
        self.setStyleSheet(f"QDialog{{background-color:{BG_CARD};}}")

        self.release_info = release_info
        self.current_version = current_version
        self.download_worker = None
        self.download_path = ""

        self._build_ui()
        self._fade_in()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 24)
        root.setSpacing(16)

        # ── Header: emerald update glyph in a tinted circle, centered ──
        badge = QLabel("⬆")
        badge.setFixedSize(56, 56)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(
            f"background-color: {GREEN_DIM}; color: {GREEN};"
            f"border: 1px solid {BORDER_ACCENT}; border-radius: 28px;"
            "font-size: 24px; font-weight: 800;"
        )
        badge_row = QHBoxLayout()
        badge_row.addStretch()
        badge_row.addWidget(badge)
        badge_row.addStretch()
        root.addLayout(badge_row)

        self.title_lbl = QLabel("Update Available")
        self.title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_lbl.setStyleSheet(f"color: {FG}; font-size: 19px; font-weight: 700; background: transparent;")
        root.addWidget(self.title_lbl)

        self.subtitle_lbl = QLabel("A new version of DevInstaller is ready to install.")
        self.subtitle_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_lbl.setWordWrap(True)
        self.subtitle_lbl.setStyleSheet(f"color: {FG_DIM}; font-size: 12px; background: transparent;")
        root.addWidget(self.subtitle_lbl)

        # ── Version comparison card: Installed → Latest ──
        version_widget = QWidget()
        version_widget.setStyleSheet(
            f"background-color: {BG_WINDOW}; border: 1px solid {BORDER}; border-radius: 8px;")
        version_layout = QHBoxLayout(version_widget)
        version_layout.setContentsMargins(16, 12, 16, 12)
        version_layout.setSpacing(8)

        current_badge = PillBadge(f"Installed  {self.current_version}", "default")
        arrow = QLabel("→")
        arrow.setStyleSheet(f"color: {FG_MUTED}; font-size: 14px; font-weight: 700; background: transparent;")
        new_badge = PillBadge(f"Latest  {self.release_info['latest_version']}", "green")

        version_layout.addStretch()
        version_layout.addWidget(current_badge)
        version_layout.addWidget(arrow)
        version_layout.addWidget(new_badge)
        version_layout.addStretch()
        root.addWidget(version_widget)

        # Release Notes Text box
        self.notes_label = QLabel("Release Notes:")
        self.notes_label.setStyleSheet(f"color: {FG_DIM}; font-size: 11px; font-weight: 600; text-transform: uppercase; background: transparent;")
        root.addWidget(self.notes_label)

        self.notes_text = QTextEdit()
        self.notes_text.setReadOnly(True)
        self.notes_text.setPlainText(self.release_info.get("body", "No release details provided."))
        self.notes_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {BG_LOG};
                color: {FG};
                border: 1px solid {BORDER};
                border-radius: 6px;
                font-family: "JetBrains Mono", "Cascadia Code", "Segoe UI", sans-serif;
                font-size: 12px;
                padding: 10px;
            }}
        """)
        root.addWidget(self.notes_text, stretch=1)

        # Progress bar & Download status (hidden initially)
        self.progress_container = QWidget()
        self.progress_container.setVisible(False)
        prog_layout = QVBoxLayout(self.progress_container)
        prog_layout.setContentsMargins(0, 0, 0, 0)
        prog_layout.setSpacing(10)

        # Status row with percentage label on the upper-right corner
        status_row = QHBoxLayout()
        status_row.setContentsMargins(0, 0, 0, 0)

        self.status_lbl = QLabel("Downloading update...")
        self.status_lbl.setStyleSheet(f"color: {FG}; font-size: 12px; font-weight: 500; background: transparent;")
        status_row.addWidget(self.status_lbl)

        status_row.addStretch()

        self.percent_lbl = QLabel("0%")
        self.percent_lbl.setStyleSheet(f"color: {GREEN}; font-size: 12px; font-weight: 700; background: transparent;")
        status_row.addWidget(self.percent_lbl)

        prog_layout.addLayout(status_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(1)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {BG_WINDOW};
                border: 1px solid {BORDER};
                border-radius: 4px;
                height: 8px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {GREEN}, stop:1 #22c55e);
                border-radius: 3px;
            }}
        """)
        prog_layout.addWidget(self.progress_bar)
        root.addWidget(self.progress_container)

        # Action Buttons Layout
        self.actions_layout = QHBoxLayout()
        self.actions_layout.setSpacing(10)
        self.actions_layout.addStretch()

        # Secondary (Later/Cancel) button — themed ghost button
        self.later_btn = ActionButton("Later", "secondary")
        self.later_btn.clicked.connect(self.reject)
        self.actions_layout.addWidget(self.later_btn)

        # Primary (Update Now) button
        has_url = bool(self.release_info.get("download_url"))
        btn_text = "Update Now" if has_url else "Open Releases"
        self.update_btn = ActionButton(btn_text, "primary")
        self.update_btn.clicked.connect(self._on_update_clicked)
        self.actions_layout.addWidget(self.update_btn)

        root.addLayout(self.actions_layout)

    def _fade_in(self) -> None:
        self.setWindowOpacity(0.0)
        self._anim = QPropertyAnimation(self, b"windowOpacity")
        self._anim.setDuration(220)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.start()

    def _on_update_clicked(self) -> None:
        download_url = self.release_info.get("download_url")
        if not download_url:
            # Fallback to opening browser releases page
            import urllib.parse
            url = self.release_info.get("html_url") or "https://github.com"
            import webbrowser
            webbrowser.open(url)
            self.accept()
            return

        # Start downloading
        self.title_lbl.setText("Downloading Update")
        self.subtitle_lbl.setText("Fetching the latest package version...")
        
        # Hide changelog text and notes label to make room/look clean
        self.notes_label.setVisible(False)
        self.notes_text.setVisible(False)
        
        # Show progress bar container
        self.progress_container.setVisible(True)
        
        # Configure button state
        self.update_btn.setEnabled(False)
        self.update_btn.setVisible(False)
        self.later_btn.setText("Cancel")
        try:
            self.later_btn.clicked.disconnect()
        except Exception:
            pass
        self.later_btn.clicked.connect(self._on_cancel_download)

        # Prepare destination file safely avoiding lock conflicts
        import time
        asset_name = self.release_info.get("asset_name") or "UniversalDevManager_update.exe"
        temp_dir = Path(tempfile.gettempdir()) / "devinstaller_updates"
        temp_dir.mkdir(parents=True, exist_ok=True)
        dest_candidate = temp_dir / asset_name
        try:
            if dest_candidate.exists():
                with open(dest_candidate, "a+b"):
                    pass
        except OSError:
            dest_candidate = temp_dir / f"update_{int(time.time())}_{asset_name}"
        self.download_path = str(dest_candidate)

        # Start download thread
        self.download_worker = UpdateDownloadWorker(download_url, self.download_path, self)
        self.download_worker.progress.connect(self._on_download_progress)
        self.download_worker.finished.connect(self._on_download_finished)
        self.download_worker.error.connect(self._on_download_failed)
        self.download_worker.start()

    def _on_download_progress(self, percent: int) -> None:
        target_val = max(1, min(100, percent))
        self._prog_anim = QPropertyAnimation(self.progress_bar, b"value")
        self._prog_anim.setDuration(180)
        self._prog_anim.setStartValue(self.progress_bar.value())
        self._prog_anim.setEndValue(target_val)
        self._prog_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        self._prog_anim.start()
        self.percent_lbl.setText(f"{target_val}%")

    def _on_download_finished(self, filepath: str) -> None:
        self.status_lbl.setText("Applying update, restarting...")
        self.percent_lbl.setText("100%")
        self.progress_bar.setValue(100)
        self.later_btn.setEnabled(False)
        
        # Launch platform-specific self-updater
        try:
            self._launch_installer(filepath)
        except Exception as e:
            self._on_download_failed(f"Failed to launch update: {e}")

    def _on_download_failed(self, error_msg: str) -> None:
        self.title_lbl.setText("Update Failed")
        self.subtitle_lbl.setText("Could not complete the automatic update.")
        
        self.progress_container.setVisible(False)
        self.notes_label.setVisible(True)
        self.notes_text.setVisible(True)
        self.notes_text.setPlainText(f"Error: {error_msg}\n\nYou can download the update manually from the releases page.")
        
        self.update_btn.setText("Open Releases")
        self.update_btn.setEnabled(True)
        self.update_btn.setVisible(True)
        self.update_btn.disconnect()
        import webbrowser
        self.update_btn.clicked.connect(lambda: [webbrowser.open(self.release_info.get("html_url") or "https://github.com"), self.accept()])
        
        self.later_btn.setText("Close")
        self.later_btn.setEnabled(True)
        self.later_btn.disconnect()
        self.later_btn.clicked.connect(self.reject)

    def _on_cancel_download(self) -> None:
        if self.download_worker and self.download_worker.isRunning():
            if hasattr(self.download_worker, "cancel"):
                self.download_worker.cancel()
            self.download_worker.wait(1500)
        self.reject()

    def _launch_installer(self, filepath: str) -> None:
        current_exe = sys.executable
        is_frozen = getattr(sys, "frozen", False)

        if sys.platform == "win32":
            if is_frozen:
                pid = os.getpid()
                # PowerShell script to wait for this process to exit, copy downloaded file with retries, and start it
                ps_script = (
                    f"$proc = Get-Process -Id {pid} -ErrorAction SilentlyContinue; "
                    f"if ($proc) {{ $proc | Wait-Process -Timeout 15 }}; "
                    f"Start-Sleep -Milliseconds 600; "
                    f"for ($i=0; $i -lt 8; $i++) {{ "
                    f"  try {{ Copy-Item -Path '{filepath}' -Destination '{current_exe}' -Force -ErrorAction Stop; break }} "
                    f"  catch {{ Start-Sleep -Milliseconds 500 }} "
                    f"}}; "
                    f"Start-Process -FilePath '{current_exe}';"
                )
                cmd = [
                    "powershell",
                    "-NoProfile",
                    "-WindowStyle",
                    "Hidden",
                    "-Command",
                    ps_script,
                ]
                subprocess.Popen(cmd, creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                # If running from source, execute the new binary separately
                os.startfile(filepath)
            
            QApplication.quit()

        elif sys.platform == "darwin":
            if filepath.endswith(".dmg"):
                subprocess.Popen(["open", filepath])
            QApplication.quit()

        else:
            # Linux - set permissions on AppImage and run
            if filepath.endswith(".AppImage"):
                try:
                    os.chmod(filepath, 0o755)
                    subprocess.Popen([filepath])
                except Exception:
                    pass
            QApplication.quit()
