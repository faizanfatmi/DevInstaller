"""DevInstaller premium dark theme — deep navy color palette and global QSS stylesheet.

Inspired by modern dark dashboards (VS Code, GitHub Desktop, JetBrains Toolbox).
Deep navy backgrounds with blue accent and vibrant category badges.
"""

# ─── Background hierarchy ────────────────────────────────────────────
BG_WINDOW = "#0c1222"
BG_SIDEBAR = "#0a0f1e"
BG_HEADER = "#0a0f1e"
BG_CARD = "#111a2e"
BG_INPUT = "#162035"
BG_ROW = "#0f1729"
BG_ROW_HOVER = "#162035"
BG_ROW_SELECTED = "#1a2744"
BG_LOG = "#0a0f1e"
BG_STATUS = "#080d1a"

# ─── Foreground ──────────────────────────────────────────────────────
FG = "#e2e8f0"
FG_DIM = "#94a3b8"
FG_MUTED = "#475569"
FG_HEADER = "#f1f5f9"

# ─── Accent (blue primary) ──────────────────────────────────────────
ACCENT_PRIMARY = "#3b82f6"
ACCENT_SECONDARY = "#60a5fa"
ACCENT_GRADIENT_START = "#3b82f6"
ACCENT_GRADIENT_END = "#2563eb"
ACCENT_GLOW = "rgba(59, 130, 246, 0.20)"

# ─── Status colors ─────────────────────────────────────────────────
GREEN = "#4ade80"
GREEN_DIM = "#0d2e1a"
GREEN_DARK = "#22c55e"
RED = "#f87171"
RED_DIM = "#2e0d1a"
AMBER = "#fbbf24"
CYAN = "#22d3ee"
PURPLE = "#a78bfa"

# ─── Borders ────────────────────────────────────────────────────────
BORDER = "#1e2d4a"
BORDER_LIGHT = "#2a3f5f"
BORDER_ACCENT = "rgba(59, 130, 246, 0.25)"

# ─── Badges ─────────────────────────────────────────────────────────
BADGE_BG = "#1e2d4a"
BADGE_GREEN_BG = "#0d2e1a"
BADGE_GREEN_FG = "#4ade80"
BADGE_AMBER_BG = "#2e2a0d"
BADGE_AMBER_FG = "#fbbf24"
BADGE_ACCENT_BG = "rgba(59, 130, 246, 0.15)"
BADGE_ACCENT_FG = "#60a5fa"

# ─── Progress ───────────────────────────────────────────────────────
PROGRESS_BG = "#1e2d4a"
PROGRESS_FG = "#3b82f6"

# ─── Scrollbar ──────────────────────────────────────────────────────
SCROLLBAR_BG = "transparent"
SCROLLBAR_FG = "#1e2d4a"

# ─── Column header ──────────────────────────────────────────────────
COLUMN_HEADER_FG = "#475569"

# ─── Sidebar ────────────────────────────────────────────────────────
SIDEBAR_ITEM_HOVER = "#111a2e"
SIDEBAR_ITEM_ACTIVE = "#162035"
SIDEBAR_ICON_COLOR = "#475569"
SIDEBAR_ICON_ACTIVE = "#3b82f6"


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
            border-color: {ACCENT_PRIMARY};
            background-color: {BG_INPUT};
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
            border: 1.5px solid #475569;
            border-radius: 4px;
            background-color: transparent;
        }}
        QCheckBox::indicator:checked {{
            background-color: #3b82f6;
            border-color: #3b82f6;
            image: none;
        }}
        QCheckBox::indicator:hover {{
            border-color: #60a5fa;
        }}

        QTextEdit {{
            background-color: {BG_LOG};
            color: {FG_DIM};
            border: none;
            font-family: "JetBrains Mono", "Cascadia Code", "Consolas", monospace;
            font-size: 12px;
            padding: 14px;
            selection-background-color: rgba(59, 130, 246, 0.25);
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
