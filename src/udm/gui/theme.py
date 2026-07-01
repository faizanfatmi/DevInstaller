"""DevInstaller premium dark theme — color palette and global QSS stylesheet."""

# ─── Background hierarchy ────────────────────────────────────────────
BG_WINDOW = "#000000"
BG_SIDEBAR = "#050505"
BG_HEADER = "#050505"
BG_CARD = "#0a0a0a"
BG_INPUT = "#111111"
BG_ROW = "#0a0a0a"
BG_ROW_HOVER = "#151515"
BG_ROW_SELECTED = "#111511"
BG_LOG = "#050505"
BG_STATUS = "#050505"

# ─── Foreground ──────────────────────────────────────────────────────
FG = "#e4e6ef"
FG_DIM = "#8890a4"
FG_MUTED = "#505770"
FG_HEADER = "#f5f6fa"

# ─── Gradient accent (primary blue-purple) ───────────────────────────
ACCENT_PRIMARY = "#6c5ce7"
ACCENT_SECONDARY = "#0984e3"
ACCENT_GRADIENT_START = "#6c5ce7"
ACCENT_GRADIENT_END = "#00b4d8"
ACCENT_GLOW = "rgba(108, 92, 231, 0.25)"

# ─── Status colors ─────────────────────────────────────────────────
GREEN = "#00e676"
GREEN_DIM = "#0d2e1a"
GREEN_DARK = "#00c853"
RED = "#ff5252"
RED_DIM = "#2e0d0d"
AMBER = "#ffab40"
CYAN = "#18ffff"
PURPLE = "#b388ff"

# ─── Borders ────────────────────────────────────────────────────────
BORDER = "#252a3a"
BORDER_LIGHT = "#2e3548"
BORDER_ACCENT = "rgba(108, 92, 231, 0.35)"

# ─── Badges ─────────────────────────────────────────────────────────
BADGE_BG = "#252a3a"
BADGE_GREEN_BG = "#0d2e1a"
BADGE_GREEN_FG = "#00e676"
BADGE_AMBER_BG = "#2e2a0d"
BADGE_AMBER_FG = "#ffab40"
BADGE_ACCENT_BG = "rgba(108, 92, 231, 0.15)"
BADGE_ACCENT_FG = "#b388ff"

# ─── Progress ───────────────────────────────────────────────────────
PROGRESS_BG = "#1e2230"
PROGRESS_FG = "#6c5ce7"

# ─── Scrollbar ──────────────────────────────────────────────────────
SCROLLBAR_BG = "transparent"
SCROLLBAR_FG = "#2e3548"

# ─── Column header ──────────────────────────────────────────────────
COLUMN_HEADER_FG = "#505770"

# ─── Sidebar ────────────────────────────────────────────────────────
SIDEBAR_ITEM_HOVER = "#1e2230"
SIDEBAR_ITEM_ACTIVE = "rgba(108, 92, 231, 0.12)"
SIDEBAR_ICON_COLOR = "#505770"
SIDEBAR_ICON_ACTIVE = "#6c5ce7"


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
            border-radius: 10px;
            padding: 11px 16px;
            font-size: 14px;
            selection-background-color: {ACCENT_PRIMARY};
        }}
        QLineEdit:focus {{
            border-color: {ACCENT_PRIMARY};
            background-color: #1a1f30;
        }}

        QComboBox {{
            background-color: {BG_INPUT};
            color: {FG};
            border: 1px solid {BORDER};
            border-radius: 10px;
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
            selection-color: {ACCENT_PRIMARY};
            outline: none;
            border-radius: 8px;
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
            border-radius: 5px;
            text-align: center;
            color: transparent;
            max-height: 6px;
        }}
        QProgressBar::chunk {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {ACCENT_GRADIENT_START}, stop:1 {ACCENT_GRADIENT_END});
            border-radius: 5px;
        }}

        QCheckBox {{
            spacing: 8px;
        }}
        QCheckBox::indicator {{
            width: 20px;
            height: 20px;
            border: 2px solid {BORDER_LIGHT};
            border-radius: 12px;
            background-color: transparent;
        }}
        QCheckBox::indicator:checked {{
            background-color: #4caf50;
            border-color: #4caf50;
            image: none;
        }}
        QCheckBox::indicator:hover {{
            border-color: #81c784;
            background-color: rgba(129, 199, 132, 0.1);
        }}

        QTextEdit {{
            background-color: {BG_LOG};
            color: {FG_DIM};
            border: none;
            font-family: "JetBrains Mono", "Cascadia Code", "Consolas", monospace;
            font-size: 12px;
            padding: 14px;
            selection-background-color: rgba(108, 92, 231, 0.3);
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
            border-radius: 8px;
            padding: 8px 24px;
            min-width: 80px;
        }}
        QMessageBox QPushButton:hover {{
            background-color: {BG_ROW_HOVER};
            border-color: {ACCENT_PRIMARY};
        }}

        QToolTip {{
            background-color: {BG_CARD};
            color: {FG};
            border: 1px solid {BORDER};
            border-radius: 6px;
            padding: 6px 10px;
            font-size: 12px;
        }}
    """
