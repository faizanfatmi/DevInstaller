"""Custom Qt widgets — PillBadge, ActionButton, SidebarButton, CountBadge."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QLabel, QPushButton, QGraphicsDropShadowEffect

from udm.gui.theme import (
    ACCENT_GRADIENT_END, ACCENT_GRADIENT_START, ACCENT_GLOW, ACCENT_PRIMARY,
    AMBER, BADGE_ACCENT_BG, BADGE_ACCENT_FG, BADGE_AMBER_BG, BADGE_AMBER_FG,
    BADGE_BG, BADGE_GREEN_BG, BADGE_GREEN_FG, BG_INPUT, BORDER, BORDER_LIGHT,
    FG, FG_DIM, FG_MUTED, GREEN, GREEN_DARK, GREEN_DIM, RED, RED_DIM,
    SIDEBAR_ITEM_ACTIVE, SIDEBAR_ITEM_HOVER,
)

# ── Blue glossy button CSS ───────────────────────────────────────────
_BLUE_BTN = """
    QPushButton {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #60a5fa, stop:0.5 #3b82f6, stop:1 #2563eb);
        color: #ffffff;
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 10px;
        padding: 11px 24px;
        font-size: 13px;
        font-weight: 700;
        letter-spacing: 0.3px;
    }
    QPushButton:hover {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #93bbfd, stop:0.5 #60a5fa, stop:1 #3b82f6);
        border: 1px solid rgba(255, 255, 255, 0.25);
    }
    QPushButton:pressed {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #3b82f6, stop:0.5 #2563eb, stop:1 #1d4ed8);
    }
    QPushButton:disabled {
        background: #162035;
        color: #475569;
        border: 1px solid #1e2d4a;
    }
"""

# ── Red glossy button CSS (same design, red palette) ────────────────
_RED_BTN = """
    QPushButton {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #f87171, stop:0.5 #ef4444, stop:1 #b91c1c);
        color: #ffffff;
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 10px;
        padding: 11px 24px;
        font-size: 13px;
        font-weight: 700;
        letter-spacing: 0.3px;
    }
    QPushButton:hover {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #fca5a5, stop:0.5 #f87171, stop:1 #ef4444);
        border: 1px solid rgba(255, 255, 255, 0.25);
    }
    QPushButton:pressed {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #ef4444, stop:0.5 #b91c1c, stop:1 #991b1b);
    }
    QPushButton:disabled {
        background: #162035;
        color: #475569;
        border: 1px solid #1e2d4a;
    }
"""

# ── Secondary / ghost button ────────────────────────────────────────
_SECONDARY_BTN = """
    QPushButton {
        background-color: rgba(255, 255, 255, 0.05);
        color: #94a3b8;
        border: 1px solid #1e2d4a;
        border-radius: 10px;
        padding: 11px 24px;
        font-size: 13px;
        font-weight: 600;
        letter-spacing: 0.3px;
    }
    QPushButton:hover {
        background-color: rgba(255, 255, 255, 0.08);
        color: #e2e8f0;
        border-color: #2a3f5f;
    }
    QPushButton:pressed {
        background-color: rgba(255, 255, 255, 0.03);
    }
    QPushButton:disabled {
        background: #162035;
        color: #475569;
        border: 1px solid #1e2d4a;
    }
"""


class PillBadge(QLabel):
    """Rounded pill-style badge label."""
    VARIANTS = {
        "default": ("transparent", FG_DIM),
        "green": (BADGE_GREEN_BG, BADGE_GREEN_FG),
        "amber": (BADGE_AMBER_BG, BADGE_AMBER_FG),
        "red": (RED_DIM, RED),
        "accent": (BADGE_ACCENT_BG, BADGE_ACCENT_FG),
        "blue": ("rgba(59, 130, 246, 0.15)", "#60a5fa"),
    }

    def __init__(self, text: str, variant: str = "default", parent=None):
        super().__init__(text, parent)
        bg, fg = self.VARIANTS.get(variant, self.VARIANTS["default"])
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg}; color: {fg};
                border-radius: 4px; padding: 4px 10px;
                font-size: 11px; font-weight: 600;
            }}
        """)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)


class CountBadge(QLabel):
    """Small rounded count badge for sidebar items."""

    def __init__(self, count: int, active: bool = False, parent=None):
        super().__init__(str(count), parent)
        self._count = count
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedHeight(22)
        self.setMinimumWidth(32)
        self.set_active(active)

    def set_active(self, active: bool):
        if active:
            self.setStyleSheet("""
                QLabel {
                    background-color: #3b82f6;
                    color: #ffffff;
                    border-radius: 11px;
                    padding: 2px 8px;
                    font-size: 11px;
                    font-weight: 700;
                }
            """)
        else:
            self.setStyleSheet("""
                QLabel {
                    background-color: rgba(255, 255, 255, 0.08);
                    color: #94a3b8;
                    border-radius: 11px;
                    padding: 2px 8px;
                    font-size: 11px;
                    font-weight: 600;
                }
            """)

    def set_count(self, count: int):
        self._count = count
        self.setText(str(count))


class ActionButton(QPushButton):
    """Glossy action button — blue for primary, red for danger, ghost for secondary."""

    def __init__(self, text: str, variant: str = "primary", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._variant = variant
        if variant == "danger":
            self.setStyleSheet(_RED_BTN)
            glow = QGraphicsDropShadowEffect(self)
            glow.setBlurRadius(18)
            glow.setColor(QColor(239, 68, 68, 60))
            glow.setOffset(0, 2)
            self.setGraphicsEffect(glow)
        elif variant == "secondary":
            self.setStyleSheet(_SECONDARY_BTN)
        else:
            self.setStyleSheet(_BLUE_BTN)
            glow = QGraphicsDropShadowEffect(self)
            glow.setBlurRadius(18)
            glow.setColor(QColor(59, 130, 246, 60))
            glow.setOffset(0, 2)
            self.setGraphicsEffect(glow)


class SidebarButton(QPushButton):
    """Sidebar navigation button — navy dark style with colored icons."""

    def __init__(self, text: str, icon_char: str = "", parent=None):
        display = f"{icon_char}  {text}" if icon_char else text
        super().__init__(display, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._active = False
        self._icon_char = icon_char
        self._text = text
        self._apply_style()

    def set_active(self, active: bool):
        self._active = active
        self._apply_style()

    def _apply_style(self):
        if self._active:
            bg = SIDEBAR_ITEM_ACTIVE
            fg = "#ffffff"
            fw = "600"
            border_left = "border-left: 3px solid #3b82f6;"
        else:
            bg = "transparent"
            fg = FG_DIM
            fw = "400"
            border_left = "border-left: 3px solid transparent;"
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg}; color: {fg};
                border: none; border-radius: 6px;
                {border_left}
                padding: 10px 16px; margin: 1px 8px;
                font-size: 13px; font-weight: {fw}; text-align: left;
            }}
            QPushButton:hover {{
                background-color: {SIDEBAR_ITEM_HOVER}; color: {FG};
            }}
        """)

    def enterEvent(self, event):
        if not self._active:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {SIDEBAR_ITEM_HOVER}; color: {FG};
                    border: none; border-radius: 6px;
                    border-left: 3px solid transparent;
                    padding: 10px 16px; margin: 1px 8px;
                    font-size: 13px; font-weight: 400; text-align: left;
                }}
            """)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._apply_style()
        super().leaveEvent(event)
