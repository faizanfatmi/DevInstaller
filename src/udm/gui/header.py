"""Header bar — app branding with clean monochrome design."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from udm.config import resource_path
from udm.constants import LOGO_FILENAME

from udm.gui.theme import (
    BG_HEADER,
    BORDER,
    FG_DIM,
    FG_HEADER,
    FG_MUTED,
)
from udm.gui.widgets import PillBadge
from udm.platform import is_admin, os_label


class HeaderBar(QWidget):
    """Top header bar with app branding and status badges — monochrome style."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            background-color: {BG_HEADER};
            border-bottom: 1px solid {BORDER};
        """)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Main header content
        header_content = QWidget()
        header_content.setFixedHeight(60)
        header_content.setStyleSheet(f"background-color: {BG_HEADER};")

        layout = QHBoxLayout(header_content)
        layout.setContentsMargins(24, 0, 24, 0)

        # App icon + name
        brand_layout = QHBoxLayout()
        brand_layout.setSpacing(12)

        # App icon — the brand logo (logo.png), with a graceful fallback.
        icon_label = QLabel()
        icon_label.setFixedSize(32, 32)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_path = resource_path(LOGO_FILENAME)
        pixmap = QPixmap(str(logo_path)) if logo_path.exists() else QPixmap()
        if not pixmap.isNull():
            icon_label.setPixmap(
                pixmap.scaled(
                    32,
                    32,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
            icon_label.setStyleSheet("background: transparent; border-radius: 6px;")
        else:
            icon_label.setText("D")
            icon_label.setStyleSheet("""
                QLabel {
                    background-color: #ffffff;
                    border-radius: 6px;
                    font-size: 16px;
                    font-weight: 800;
                    color: #0d0d0d;
                }
            """)
        brand_layout.addWidget(icon_label)

        # Title + subtitle
        title_block = QVBoxLayout()
        title_block.setSpacing(0)

        title = QLabel("DevInstaller")
        title.setStyleSheet(f"""
            color: {FG_HEADER};
            font-size: 18px;
            font-weight: 700;
            letter-spacing: 0.3px;
            background: transparent;
        """)
        title_block.addWidget(title)

        subtitle = QLabel("Developer Tools Package Manager")
        subtitle.setStyleSheet(f"""
            color: {FG_MUTED};
            font-size: 11px;
            font-weight: 400;
            letter-spacing: 0.2px;
            background: transparent;
        """)
        title_block.addWidget(subtitle)

        brand_layout.addLayout(title_block)
        layout.addLayout(brand_layout)

        layout.addStretch()

        # Badges with platform-specific OS and user icons, matching the monochrome theme
        from udm.platform import detect_os
        current_os = detect_os()
        if current_os == "Windows":
            os_text = "  🪟 WINDOWS"
        elif current_os == "Darwin":
            os_text = "  🍎 macOS"
        else:
            os_text = "  🐧 LINUX"
            
        os_badge = PillBadge(os_text, "default")
        layout.addWidget(os_badge)

        layout.addSpacing(8)

        if is_admin():
            admin_text = "  👤 ADMIN"
        else:
            admin_text = "  👤 USER"
            
        admin_badge = PillBadge(admin_text, "default")
        layout.addWidget(admin_badge)

        outer.addWidget(header_content)
