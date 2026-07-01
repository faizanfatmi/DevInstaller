"""Header bar — app branding with gradient accent line."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QLinearGradient, QPainter, QColor, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from udm.config import resource_path
from udm.constants import LOGO_FILENAME

from udm.gui.theme import (
    ACCENT_GRADIENT_END,
    ACCENT_GRADIENT_START,
    ACCENT_PRIMARY,
    BG_HEADER,
    BORDER,
    FG_DIM,
    FG_HEADER,
    FG_MUTED,
)
from udm.gui.widgets import PillBadge
from udm.platform import is_admin, os_label


class GradientLine(QWidget):
    """Thin horizontal gradient accent line."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(2)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0.0, QColor(ACCENT_GRADIENT_START))
        gradient.setColorAt(0.5, QColor(ACCENT_GRADIENT_END))
        gradient.setColorAt(1.0, QColor(ACCENT_GRADIENT_START))
        painter.fillRect(self.rect(), gradient)
        painter.end()


class HeaderBar(QWidget):
    """Top header bar with app branding and status badges."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {BG_HEADER}; border: none;")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Main header content
        header_content = QWidget()
        header_content.setFixedHeight(64)
        header_content.setStyleSheet(f"background-color: {BG_HEADER};")

        layout = QHBoxLayout(header_content)
        layout.setContentsMargins(28, 0, 28, 0)

        # App icon + name
        brand_layout = QHBoxLayout()
        brand_layout.setSpacing(12)

        # App icon — the brand logo (logo.png), with a graceful fallback.
        icon_label = QLabel()
        icon_label.setFixedSize(36, 36)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_path = resource_path(LOGO_FILENAME)
        pixmap = QPixmap(str(logo_path)) if logo_path.exists() else QPixmap()
        if not pixmap.isNull():
            icon_label.setPixmap(
                pixmap.scaled(
                    36,
                    36,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
            icon_label.setStyleSheet("background: transparent; border-radius: 10px;")
        else:
            icon_label.setText("D")
            icon_label.setStyleSheet(f"""
                QLabel {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 {ACCENT_GRADIENT_START}, stop:1 {ACCENT_GRADIENT_END});
                    border-radius: 10px;
                    font-size: 18px;
                    font-weight: 800;
                    color: white;
                }}
            """)
        brand_layout.addWidget(icon_label)

        # Title + subtitle
        title_block = QVBoxLayout()
        title_block.setSpacing(0)

        title = QLabel("DevInstaller")
        title.setStyleSheet(f"""
            color: {FG_HEADER};
            font-size: 20px;
            font-weight: 800;
            letter-spacing: 0.5px;
            background: transparent;
        """)
        title_block.addWidget(title)

        subtitle = QLabel("Developer Tools Package Manager")
        subtitle.setStyleSheet(f"""
            color: {FG_MUTED};
            font-size: 11px;
            font-weight: 500;
            letter-spacing: 0.3px;
            background: transparent;
        """)
        title_block.addWidget(subtitle)

        brand_layout.addLayout(title_block)
        layout.addLayout(brand_layout)

        layout.addStretch()

        # Badges
        os_text = f"  {os_label().upper()}"
        os_badge = PillBadge(os_text, "default")
        layout.addWidget(os_badge)

        layout.addSpacing(8)

        if is_admin():
            admin_badge = PillBadge("🔓  ADMIN", "green")
        else:
            admin_badge = PillBadge("🔒  USER", "amber")
        layout.addWidget(admin_badge)

        outer.addWidget(header_content)

        # Gradient accent line
        gradient_line = GradientLine()
        outer.addWidget(gradient_line)
