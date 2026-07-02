"""Custom Qt widgets — PillBadge, ActionButton, SidebarButton."""

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

# ── Green glossy button CSS ──────────────────────────────────────────
_GREEN_BTN = """
    QPushButton {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #4ade80, stop:0.5 #22c55e, stop:1 #16a34a);
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
            stop:0 #86efac, stop:0.5 #4ade80, stop:1 #22c55e);
        border: 1px solid rgba(255, 255, 255, 0.25);
    }
    QPushButton:pressed {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #22c55e, stop:0.5 #16a34a, stop:1 #15803d);
    }
    QPushButton:disabled {
        background: #1a1a1a;
        color: #555555;
        border: 1px solid #1f1f1f;
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
        background: #1a1a1a;
        color: #555555;
        border: 1px solid #1f1f1f;
    }
"""


class PillBadge(QLabel):
    """Rounded pill-style badge label."""
    VARIANTS = {
        "default": ("transparent", FG_DIM),
        "green": (BADGE_GREEN_BG, BADGE_GREEN_FG),
        "amber": (BADGE_AMBER_BG, BADGE_AMBER_FG),
        "red": (RED_DIM, RED),
        "accent": ("transparent", BADGE_ACCENT_FG),
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


class ActionButton(QPushButton):
    """Glossy action button — green for primary/secondary, red for danger."""

    def __init__(self, text: str, variant: str = "primary", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._variant = variant
        if variant == "danger":
            self.setStyleSheet(_RED_BTN)
            glow = QGraphicsDropShadowEffect(self)
            glow.setBlurRadius(18)
            glow.setColor(QColor(239, 68, 68, 80))
            glow.setOffset(0, 2)
            self.setGraphicsEffect(glow)
        else:
            self.setStyleSheet(_GREEN_BTN)
            glow = QGraphicsDropShadowEffect(self)
            glow.setBlurRadius(18)
            glow.setColor(QColor(34, 197, 94, 80))
            glow.setOffset(0, 2)
            self.setGraphicsEffect(glow)


class SidebarButton(QPushButton):
    """Sidebar navigation button — clean monochrome style."""

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
            bg, fg, fw = SIDEBAR_ITEM_ACTIVE, "#ffffff", "600"
        else:
            bg, fg, fw = "transparent", FG_DIM, "400"
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg}; color: {fg};
                border: none; border-radius: 6px;
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
                    padding: 10px 16px; margin: 1px 8px;
                    font-size: 13px; font-weight: 400; text-align: left;
                }}
            """)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._apply_style()
        super().leaveEvent(event)
