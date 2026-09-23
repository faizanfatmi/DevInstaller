"""Dialog prompting user to paste or browse the Oracle SQL Developer archive/folder path."""

from __future__ import annotations

import glob
import os

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from udm.gui.theme import (
    ACCENT_PRIMARY,
    BG_CARD,
    BG_INPUT,
    BG_WINDOW,
    BORDER,
    FG,
    FG_DIM,
    FG_MUTED,
    GREEN,
    RED,
)
from udm.gui.widgets import ActionButton


def _detect_default_sqldeveloper_path() -> str:
    """Check common directories for an existing SQL Developer archive."""
    candidates = []
    # User Downloads
    downloads = os.path.join(os.environ.get("USERPROFILE", os.path.expanduser("~")), "Downloads")
    if os.path.isdir(downloads):
        candidates.extend(glob.glob(os.path.join(downloads, "*sqldeveloper*.zip")))
        candidates.extend(glob.glob(os.path.join(downloads, "*SQLDeveloper*.zip")))

    # User Desktop
    desktop = os.path.join(os.environ.get("USERPROFILE", os.path.expanduser("~")), "Desktop")
    if os.path.isdir(desktop):
        candidates.extend(glob.glob(os.path.join(desktop, "*sqldeveloper*.zip")))

    # Current directory
    candidates.extend(glob.glob("*sqldeveloper*.zip"))

    valid = [c for c in candidates if os.path.isfile(c) and os.path.getsize(c) > 10 * 1024 * 1024]
    if valid:
        valid.sort(key=lambda p: os.path.getmtime(p), reverse=True)
        return valid[0]
    return ""


class OraclePathDialog(QDialog):
    """Modern modal dialog allowing user to paste or browse for Oracle SQL Developer."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Oracle SQL Developer Setup")
        self.setModal(True)
        self.setMinimumWidth(560)
        self.setStyleSheet(f"QDialog {{ background-color: {BG_CARD}; }}")

        self._build_ui()
        default_path = _detect_default_sqldeveloper_path()
        if default_path:
            self.path_input.setText(default_path)
            self._validate_path(default_path)
        else:
            self._validate_path("")

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        # Header Title
        title_lbl = QLabel("Oracle SQL Developer Installation")
        title_lbl.setStyleSheet(
            f"color: {FG}; font-size: 18px; font-weight: 700; background: transparent;"
        )
        root.addWidget(title_lbl)

        subtitle_lbl = QLabel(
            "Official direct download links are available (with JDK included). "
            "You can download automatically, or paste/browse a local file."
        )
        subtitle_lbl.setWordWrap(True)
        subtitle_lbl.setStyleSheet(
            f"color: {FG_DIM}; font-size: 12px; line-height: 1.4; background: transparent;"
        )
        root.addWidget(subtitle_lbl)

        # Instruction card
        card = QWidget()
        card.setStyleSheet(
            f"background-color: {BG_WINDOW}; border: 1px solid {BORDER}; border-radius: 8px;"
        )
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 14, 16, 14)
        card_layout.setSpacing(10)

        step1 = QLabel(
            "• <b>Automatic:</b> Leave the path blank and click <b>Download & Install</b>.<br>"
            "• <b>Local File:</b> Paste or browse to your downloaded <code>sqldeveloper.zip</code>."
        )
        step1.setWordWrap(True)
        step1.setStyleSheet(f"color: {FG}; font-size: 12px; border: none; background: transparent;")
        card_layout.addWidget(step1)

        dl_btn = QPushButton("Open Oracle Download Page ↗")
        dl_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        dl_btn.setStyleSheet(
            f"QPushButton {{ background-color: transparent; color: {ACCENT_PRIMARY}; "
            f"border: 1px solid {BORDER}; border-radius: 6px; padding: 6px 12px; "
            f"font-size: 12px; font-weight: 600; text-align: left; }} "
            f"QPushButton:hover {{ border-color: {ACCENT_PRIMARY}; background-color: rgba(111, 221, 120, 0.1); }}"
        )
        dl_btn.clicked.connect(self._open_oracle_url)
        card_layout.addWidget(dl_btn)

        note_lbl = QLabel(
            "ℹ <i>No administrator privileges or policy bypass required. DevInstaller installs SQL Developer cleanly into your user space.</i>"
        )
        note_lbl.setWordWrap(True)
        note_lbl.setStyleSheet(f"color: {FG_MUTED}; font-size: 11px; border: none; background: transparent;")
        card_layout.addWidget(note_lbl)

        root.addWidget(card)

        # Input label
        input_lbl = QLabel("Local archive path (optional — leave blank for direct download):")
        input_lbl.setStyleSheet(f"color: {FG}; font-size: 12px; background: transparent;")
        root.addWidget(input_lbl)

        # Path input row
        input_row = QHBoxLayout()
        input_row.setSpacing(10)

        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText(r"Leave blank to download automatically, or paste path...")
        self.path_input.setStyleSheet(
            f"QLineEdit {{ background-color: {BG_INPUT}; color: {FG}; "
            f"border: 1px solid {BORDER}; border-radius: 6px; padding: 8px 12px; "
            f"font-size: 12px; }} "
            f"QLineEdit:focus {{ border-color: {ACCENT_PRIMARY}; }}"
        )
        self.path_input.textChanged.connect(self._validate_path)
        input_row.addWidget(self.path_input)

        browse_btn = QPushButton("Browse…")
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.setStyleSheet(
            f"QPushButton {{ background-color: {BG_WINDOW}; color: {FG}; "
            f"border: 1px solid {BORDER}; border-radius: 6px; padding: 8px 14px; "
            f"font-size: 12px; font-weight: 600; }} "
            f"QPushButton:hover {{ border-color: {ACCENT_PRIMARY}; }}"
        )
        browse_btn.clicked.connect(self._browse_file)
        input_row.addWidget(browse_btn)

        root.addLayout(input_row)

        # Validation status label
        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet("font-size: 11px; background: transparent;")
        root.addWidget(self.status_lbl)

        root.addSpacing(4)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addStretch()

        self.cancel_btn = ActionButton("Cancel", "secondary")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.install_btn = ActionButton("Download & Install", "primary")
        self.install_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.install_btn)

        root.addLayout(btn_layout)

    def _open_oracle_url(self) -> None:
        QDesktopServices.openUrl(
            QUrl("https://www.oracle.com/tools/downloads/sqldev-downloads.html")
        )

    def _browse_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Oracle SQL Developer ZIP Archive",
            os.path.join(os.environ.get("USERPROFILE", os.path.expanduser("~")), "Downloads"),
            "ZIP Archives (*.zip);;All Files (*.*)",
        )
        if path:
            self.path_input.setText(path)
            self._validate_path(path)

    def _validate_path(self, text: str) -> None:
        clean = text.strip().strip('"').strip("'")
        if not clean:
            self.status_lbl.setText("Direct download will be performed automatically (~500 MB).")
            self.status_lbl.setStyleSheet(f"color: {ACCENT_PRIMARY}; font-size: 11px;")
            self.install_btn.setText("Download & Install")
            self.install_btn.setEnabled(True)
            return

        expanded = os.path.expanduser(os.path.expandvars(clean))
        if os.path.isfile(expanded):
            self.status_lbl.setText("✓ Valid archive file detected.")
            self.status_lbl.setStyleSheet(f"color: {GREEN}; font-size: 11px; font-weight: 600;")
            self.install_btn.setText("Install from File")
            self.install_btn.setEnabled(True)
        elif os.path.isdir(expanded):
            self.status_lbl.setText("✓ Valid directory detected.")
            self.status_lbl.setStyleSheet(f"color: {GREEN}; font-size: 11px; font-weight: 600;")
            self.install_btn.setText("Install from Directory")
            self.install_btn.setEnabled(True)
        else:
            self.status_lbl.setText("✗ Specified path does not exist on disk.")
            self.status_lbl.setStyleSheet(f"color: {RED}; font-size: 11px;")
            self.install_btn.setEnabled(False)

    def get_path(self) -> str:
        """Return the cleaned, normalized path entered by the user."""
        raw = self.path_input.text().strip().strip('"').strip("'")
        return os.path.expanduser(os.path.expandvars(raw))
