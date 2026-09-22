"""Header bar — app branding, OS selector, and user avatar."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from udm.config import resource_path
from udm.constants import LOGO_FILENAME

from udm.gui.theme import (
    BG_HEADER,
    BORDER,
    FG,
    FG_DIM,
    FG_HEADER,
    FG_MUTED,
)
from udm.gui.widgets import PillBadge
from udm.platform import is_admin, os_label


class HeaderBar(QWidget):
    """Top header bar with app branding, OS selector, and user avatar — navy style."""

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
        layout.setContentsMargins(20, 0, 20, 0)

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
            icon_label.setStyleSheet("background: transparent; border-radius: 8px;")
        else:
            icon_label.setText("D")
            icon_label.setStyleSheet("""
                QLabel {
                    background-color: #3b82f6;
                    border-radius: 8px;
                    font-size: 18px;
                    font-weight: 800;
                    color: #ffffff;
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

        # ── OS badge with dropdown arrow ──
        from udm.platform import detect_os
        current_os = detect_os()
        if current_os == "Windows":
            os_icon = "🪟"
            os_text = "Windows"
        elif current_os == "Darwin":
            os_icon = "🍎"
            os_text = "macOS"
        else:
            os_icon = "🐧"
            os_text = "Linux"

        os_badge = QLabel(f"  {os_icon}  {os_text}  ▾")
        os_badge.setCursor(Qt.CursorShape.PointingHandCursor)
        os_badge.setStyleSheet(f"""
            QLabel {{
                background-color: rgba(255, 255, 255, 0.05);
                color: {FG};
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 600;
            }}
        """)
        layout.addWidget(os_badge)

        layout.addSpacing(12)

        # ── User profile avatar ──
        user_section = QWidget()
        user_section.setStyleSheet("background: transparent;")
        user_layout = QHBoxLayout(user_section)
        user_layout.setContentsMargins(0, 0, 0, 0)
        user_layout.setSpacing(8)

        avatar = QLabel("F")
        avatar.setFixedSize(34, 34)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #3b82f6, stop:1 #8b5cf6);
                color: #ffffff;
                border-radius: 17px;
                font-size: 14px;
                font-weight: 700;
            }
        """)
        user_layout.addWidget(avatar)

        user_info = QVBoxLayout()
        user_info.setSpacing(0)

        import os
        username = os.environ.get("USERNAME", os.environ.get("USER", "User"))
        user_name = QLabel(username.capitalize())
        user_name.setStyleSheet(f"""
            color: {FG};
            font-size: 12px;
            font-weight: 600;
            background: transparent;
        """)
        user_info.addWidget(user_name)

        user_role = QLabel("Developer")
        user_role.setStyleSheet(f"""
            color: {FG_MUTED};
            font-size: 10px;
            background: transparent;
        """)
        user_info.addWidget(user_role)

        user_layout.addLayout(user_info)

        dropdown_arrow = QLabel("▾")
        dropdown_arrow.setStyleSheet(f"""
            color: {FG_MUTED};
            font-size: 10px;
            background: transparent;
        """)
        user_layout.addWidget(dropdown_arrow)

        layout.addWidget(user_section)

        outer.addWidget(header_content)
