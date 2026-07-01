"""Status bar — gradient progress bar + system status label."""

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QWidget

from udm.constants import APP_VERSION
from udm.gui.theme import (
    ACCENT_GRADIENT_END,
    ACCENT_GRADIENT_START,
    ACCENT_PRIMARY,
    BG_STATUS,
    BORDER,
    FG_DIM,
    FG_MUTED,
    PROGRESS_BG,
)
from udm.gui.widgets import PillBadge


class StatusBar(QWidget):
    """Bottom status bar with gradient progress indicator."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(38)
        self.setStyleSheet(f"""
            background-color: {BG_STATUS};
            border-top: 1px solid {BORDER};
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(28, 0, 28, 0)
        layout.setSpacing(12)

        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet(f"""
            color: {FG_MUTED};
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.5px;
            background: transparent;
        """)
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {PROGRESS_BG};
                border: none;
                border-radius: 3px;
                max-height: 6px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {ACCENT_GRADIENT_START}, stop:1 {ACCENT_GRADIENT_END});
                border-radius: 3px;
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
