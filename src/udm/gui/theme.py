"""DevInstaller premium dark theme — monochrome color palette and global QSS stylesheet.

Inspired by modern dark dashboards (Linear, Vercel, beast insights).
Clean monochrome design with true-black backgrounds and white/gray text hierarchy.
"""

# ─── Background hierarchy ────────────────────────────────────────────
BG_WINDOW = "#0d0d0d"
BG_SIDEBAR = "#0f0f0f"
BG_HEADER = "#0f0f0f"
BG_CARD = "#151515"
BG_INPUT = "#1a1a1a"
BG_ROW = "#111111"
BG_ROW_HOVER = "#1a1a1a"
BG_ROW_SELECTED = "#1a1f1a"
BG_LOG = "#0f0f0f"
BG_STATUS = "#0a0a0a"

# ─── Foreground ──────────────────────────────────────────────────────
FG = "#e8e8e8"
FG_DIM = "#999999"
FG_MUTED = "#555555"
FG_HEADER = "#ffffff"

# ─── Accent (clean monochrome with subtle blue for interactive) ──────
ACCENT_PRIMARY = "#ffffff"
ACCENT_SECONDARY = "#cccccc"
ACCENT_GRADIENT_START = "#ffffff"
ACCENT_GRADIENT_END = "#cccccc"
ACCENT_GLOW = "rgba(255, 255, 255, 0.15)"

# ─── Status colors ─────────────────────────────────────────────────
GREEN = "#4ade80"
GREEN_DIM = "#0d2e1a"
GREEN_DARK = "#22c55e"
RED = "#f87171"
RED_DIM = "#2e0d0d"
AMBER = "#fbbf24"
CYAN = "#22d3ee"
PURPLE = "#a78bfa"

# ─── Borders ────────────────────────────────────────────────────────
BORDER = "#1f1f1f"
BORDER_LIGHT = "#2a2a2a"
BORDER_ACCENT = "rgba(255, 255, 255, 0.12)"

# ─── Badges ─────────────────────────────────────────────────────────
BADGE_BG = "#1f1f1f"
BADGE_GREEN_BG = "#0d2e1a"
BADGE_GREEN_FG = "#4ade80"
BADGE_AMBER_BG = "#2e2a0d"
BADGE_AMBER_FG = "#fbbf24"
BADGE_ACCENT_BG = "rgba(255, 255, 255, 0.08)"
BADGE_ACCENT_FG = "#cccccc"

# ─── Progress ───────────────────────────────────────────────────────
PROGRESS_BG = "#1a1a1a"
PROGRESS_FG = "#ffffff"

# ─── Scrollbar ──────────────────────────────────────────────────────
SCROLLBAR_BG = "transparent"
SCROLLBAR_FG = "#2a2a2a"

# ─── Column header ──────────────────────────────────────────────────
COLUMN_HEADER_FG = "#555555"

# ─── Sidebar ────────────────────────────────────────────────────────
SIDEBAR_ITEM_HOVER = "#1a1a1a"
SIDEBAR_ITEM_ACTIVE = "rgba(255, 255, 255, 0.08)"
SIDEBAR_ICON_COLOR = "#555555"
SIDEBAR_ICON_ACTIVE = "#ffffff"


def build_stylesheet() -> str:
    """Return the global QSS stylesheet for the application.

    Delegates to the Windows 11 Fluent Design theme. Legacy colour constants in
    this module are preserved for widgets that still import them directly.
    """
    from udm.gui.fluent import fluent_stylesheet

    return fluent_stylesheet()


def _legacy_stylesheet() -> str:
    """The original premium dark stylesheet, kept for reference/fallback."""
    return f"""
        * {{
            font-family: "Segoe UI", "SF Pro Display", "Inter", "Helvetica Neue", sans-serif;
        }}
        QMainWindow {{
            background-color: {BG_WINDOW};
            color: {FG};
            font-size: 13px;
        }}
        QWidget {{
            color: {FG};
            font-size: 13px;
        }}

        QLineEdit {{
            background-color: {BG_INPUT};
            color: {FG};
            border: 1px solid {BORDER};
            border-radius: 6px;
            padding: 11px 16px;
            font-size: 14px;
            selection-background-color: {ACCENT_PRIMARY};
        }}
        QLineEdit:focus {{
            border-color: {BORDER_LIGHT};
            background-color: #1a1a1a;
        }}

        QComboBox {{
            background-color: {BG_INPUT};
            color: {FG};
            border: 1px solid {BORDER};
            border-radius: 6px;
            padding: 9px 14px;
            font-size: 13px;
            min-width: 80px;
        }}
        QComboBox:hover {{
            border-color: {BORDER_LIGHT};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 24px;
        }}
        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid {FG_DIM};
            margin-right: 10px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {BG_CARD};
            color: {FG};
            border: 1px solid {BORDER};
            selection-background-color: {SIDEBAR_ITEM_ACTIVE};
            selection-color: {FG};
            outline: none;
            border-radius: 6px;
        }}

        QScrollBar:vertical {{
            background: {SCROLLBAR_BG};
            width: 8px;
            border: none;
            border-radius: 4px;
            margin: 4px 2px;
        }}
        QScrollBar::handle:vertical {{
            background: {SCROLLBAR_FG};
            border-radius: 4px;
            min-height: 40px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {FG_MUTED};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: none;
        }}

        QProgressBar {{
            background-color: {PROGRESS_BG};
            border: none;
            border-radius: 3px;
            text-align: center;
            color: transparent;
            max-height: 4px;
        }}
        QProgressBar::chunk {{
            background-color: {PROGRESS_FG};
            border-radius: 3px;
        }}

        QCheckBox {{
            spacing: 8px;
        }}
        QCheckBox::indicator {{
            width: 20px;
            height: 20px;
            border: 1.5px solid #666666;
            border-radius: 10px;
            background-color: transparent;
        }}
        QCheckBox::indicator:checked {{
            background-color: #22c55e;
            border-color: #22c55e;
            image: none;
        }}
        QCheckBox::indicator:hover {{
            border-color: #999999;
        }}

        QTextEdit {{
            background-color: {BG_LOG};
            color: {FG_DIM};
            border: none;
            font-family: "JetBrains Mono", "Cascadia Code", "Consolas", monospace;
            font-size: 12px;
            padding: 14px;
            selection-background-color: rgba(255, 255, 255, 0.15);
        }}

        QMessageBox {{
            background-color: {BG_CARD};
        }}
        QMessageBox QLabel {{
            color: {FG};
        }}
        QMessageBox QPushButton {{
            background-color: {BG_INPUT};
            color: {FG};
            border: 1px solid {BORDER};
            border-radius: 6px;
            padding: 8px 24px;
            min-width: 80px;
        }}
        QMessageBox QPushButton:hover {{
            background-color: {BG_ROW_HOVER};
            border-color: {BORDER_LIGHT};
        }}

        QToolTip {{
            background-color: {BG_CARD};
            color: {FG};
            border: 1px solid {BORDER};
            border-radius: 4px;
            padding: 6px 10px;
            font-size: 12px;
        }}
    """
