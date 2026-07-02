"""Modern post-installation completion screen — monochrome dark theme.

Replaces the plain QMessageBox result popup with a themed summary dialog that
clearly communicates the outcome (all-success vs. completed-with-errors),
shows per-status counts, and lists any failed items.
"""

from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QVBoxLayout, QWidget,
)

from udm.gui.theme import (
    AMBER, BG_CARD, BG_WINDOW, BORDER, FG, FG_DIM, FG_MUTED, GREEN, RED,
)
from udm.gui.widgets import ActionButton


class _StatCard(QWidget):
    def __init__(self, value, label, color, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"background-color:{BG_WINDOW};"
            f"border:1px solid {BORDER};border-radius:8px;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(2)
        value_lbl = QLabel(str(value))
        value_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_lbl.setStyleSheet(
            f"color:{color};font-size:26px;font-weight:800;background:transparent;")
        layout.addWidget(value_lbl)
        name_lbl = QLabel(label)
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_lbl.setStyleSheet(
            f"color:{FG_MUTED};font-size:11px;font-weight:600;"
            "letter-spacing:0.5px;background:transparent;")
        layout.addWidget(name_lbl)


class CompletionDialog(QDialog):
    def __init__(self, installed, skipped, failed, failed_names=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Installation Complete")
        self.setModal(True)
        self.setMinimumWidth(440)
        self.setStyleSheet(f"QDialog{{background-color:{BG_CARD};}}")
        has_failures = failed > 0
        accent = AMBER if has_failures else GREEN
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 24)
        root.setSpacing(18)
        icon = QLabel("⚠" if has_failures else "✓")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet(
            f"color:{accent};font-size:44px;font-weight:800;background:transparent;")
        root.addWidget(icon)
        title = QLabel(
            "Completed with errors" if has_failures else "All done — happy coding!")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            f"color:{FG};font-size:18px;font-weight:700;background:transparent;")
        root.addWidget(title)
        subtitle = QLabel(
            "Some tools could not be installed." if has_failures
            else "Your development environment is ready.")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(
            f"color:{FG_DIM};font-size:12px;background:transparent;")
        root.addWidget(subtitle)
        cards = QHBoxLayout()
        cards.setSpacing(12)
        cards.addWidget(_StatCard(installed, "INSTALLED", GREEN))
        cards.addWidget(_StatCard(skipped, "PRESENT", FG_DIM))
        cards.addWidget(_StatCard(failed, "FAILED", RED if has_failures else FG_MUTED))
        root.addLayout(cards)
        if has_failures and failed_names:
            failed_lbl = QLabel("Failed: " + ", ".join(failed_names))
            failed_lbl.setWordWrap(True)
            failed_lbl.setStyleSheet(
                f"color:{RED};font-size:12px;background:transparent;")
            root.addWidget(failed_lbl)
        actions = QHBoxLayout()
        actions.addStretch()
        done_btn = ActionButton("Done", "primary")
        done_btn.clicked.connect(self.accept)
        actions.addWidget(done_btn)
        root.addLayout(actions)
        self._fade_in()

    def _fade_in(self):
        self.setWindowOpacity(0.0)
        self._anim = QPropertyAnimation(self, b"windowOpacity")
        self._anim.setDuration(220)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.start()
