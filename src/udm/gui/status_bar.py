"""Status bar — monochrome progress bar + system status label."""

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QWidget

from udm.constants import APP_VERSION
from udm.gui.theme import (
    BG_STATUS,
    BORDER,
    FG_DIM,
    FG_MUTED,
    PROGRESS_BG,
)
from udm.gui.widgets import PillBadge


class StatusBar(QWidget):
    """Bottom status bar with clean monochrome progress indicator."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(36)
        self.setStyleSheet(f"""
            background-color: {BG_STATUS};
            border-top: 1px solid {BORDER};
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(12)

        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet(f"""
            color: {FG_MUTED};
            font-size: 11px;
            font-weight: 500;
            letter-spacing: 0.3px;
            background: transparent;
        """)
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {PROGRESS_BG};
                border: none;
                border-radius: 1px;
                max-height: 3px;
            }}
            QProgressBar::chunk {{
                background-color: #ffffff;
                border-radius: 1px;
            }}
        """)
        layout.addWidget(self.progress_bar, stretch=1)

        # Smoothly animate value changes instead of snapping.
        self._progress_anim = QPropertyAnimation(self.progress_bar, b"value")
        self._progress_anim.setDuration(280)
        self._progress_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        layout.addSpacing(16)

        version_badge = PillBadge(f"v{APP_VERSION}", "accent")
        layout.addWidget(version_badge)

    def set_progress(self, value: int):
        """Animate the progress bar towards *value* for a smoother feel."""
        value = max(0, min(100, int(value)))
        self._progress_anim.stop()
        self._progress_anim.setStartValue(self.progress_bar.value())
        self._progress_anim.setEndValue(value)
        self._progress_anim.start()

    def set_status_text(self, text: str):
        self.status_label.setText(text)
