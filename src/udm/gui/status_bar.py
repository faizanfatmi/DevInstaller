"""Status bar — branded footer with version, package count, and tagline."""

from pathlib import Path

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QWidget

from udm.config import resource_path
from udm.constants import APP_VERSION, LOGO_FILENAME
from udm.gui.theme import (
    BG_STATUS,
    BORDER,
    FG_DIM,
    FG_MUTED,
    PROGRESS_BG,
)
from udm.gui.widgets import PillBadge


class StatusBar(QWidget):
    """Bottom status bar with app branding, package count, and developer tagline."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(36)
        self.setStyleSheet(f"""
            background-color: {BG_STATUS};
            border-top: 1px solid {BORDER};
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(8)

        # Left: App icon + version
        app_icon = QLabel()
        app_icon.setFixedSize(14, 14)
        app_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_path = resource_path(LOGO_FILENAME)
        pixmap = QPixmap(str(logo_path)) if logo_path.exists() else QPixmap()
        if pixmap.isNull():
            gear_icon = Path(__file__).resolve().parent.parent / "assets" / "icons" / "meta_gear.png"
            if gear_icon.exists():
                pixmap = QPixmap(str(gear_icon))
        if not pixmap.isNull():
            app_icon.setPixmap(
                pixmap.scaled(
                    14,
                    14,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        app_icon.setStyleSheet("background: transparent;")
        layout.addWidget(app_icon)

        version_label = QLabel(f"DevInstaller v{APP_VERSION}")
        version_label.setStyleSheet(f"""
            color: {FG_MUTED};
            font-size: 11px;
            font-weight: 500;
            background: transparent;
        """)
        layout.addWidget(version_label)

        divider = QLabel("|")
        divider.setStyleSheet("color: #3e4a3d; font-size: 11px; background: transparent; padding: 0 4px;")
        layout.addWidget(divider)

        # Center: Package count (will be updated externally)
        self.package_count_label = QLabel("129 packages available")
        self.package_count_label.setStyleSheet(f"""
            color: {FG_MUTED};
            font-size: 11px;
            font-weight: 400;
            background: transparent;
        """)
        layout.addWidget(self.package_count_label)

        layout.addStretch()

        # Progress container for installation/downloading (visible during active progress)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setFixedWidth(160)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {PROGRESS_BG};
                border: 1px solid {BORDER};
                border-radius: 3px;
                max-height: 6px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4ade80, stop:1 #22c55e);
                border-radius: 2px;
            }}
        """)
        layout.addWidget(self.progress_bar)

        # Percentage label next to progress bar
        self.percent_label = QLabel("0%")
        self.percent_label.setStyleSheet("""
            color: #4ade80;
            font-size: 11px;
            font-weight: 700;
            background: transparent;
            padding-left: 2px;
            padding-right: 6px;
        """)
        self.percent_label.setVisible(False)
        layout.addWidget(self.percent_label)

        # Smoothly animate value changes instead of snapping. Kept short so the
        # frequent live-progress updates during an install don't visibly lag.
        self._progress_anim = QPropertyAnimation(self.progress_bar, b"value")
        self._progress_anim.setDuration(140)
        self._progress_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Status text (hidden by default, shown during install)
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"""
            color: {FG_DIM};
            font-size: 11px;
            font-weight: 500;
            background: transparent;
        """)
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)

        # Right: Tagline with author credit
        tagline = QLabel("Made for developers, by developers  ·  Author by <b>Faizan-Fatmi</b>")
        tagline.setStyleSheet(f"""
            color: {FG_MUTED};
            font-size: 11px;
            font-weight: 400;
            background: transparent;
        """)
        layout.addWidget(tagline)

    def set_package_count(self, count: int):
        """Update the package count display."""
        self.package_count_label.setText(f"{count} packages available")

    def set_progress(self, value: int):
        """Animate the progress bar towards *value* and update the percentage label."""
        value = max(0, min(100, int(value)))
        is_active = (0 < value < 100)
        self.progress_bar.setVisible(is_active)
        self.percent_label.setVisible(is_active)
        if is_active:
            self.percent_label.setText(f"{value}%")
        self._progress_anim.stop()
        self._progress_anim.setStartValue(self.progress_bar.value())
        self._progress_anim.setEndValue(value)
        self._progress_anim.start()

    def set_status_text(self, text: str):
        self.status_label.setText(text)
        self.status_label.setVisible(bool(text))
