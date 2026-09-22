"""DevInstaller DevForge Dark theme — obsidian & charcoal palette with emerald accents."""

# ─── Background hierarchy ────────────────────────────────────────────
BG_WINDOW = "#101319"
BG_SIDEBAR = "#0b0e14"
BG_HEADER = "#0b0e14"
BG_CARD = "#191c22"
BG_INPUT = "#191c22"
BG_ROW = "#191c22"
BG_ROW_HOVER = "#272a31"
BG_ROW_SELECTED = "#1d2026"
BG_LOG = "#0b0e14"
BG_STATUS = "#0b0e14"

# ─── Foreground ──────────────────────────────────────────────────────
FG = "#e1e2eb"
FG_DIM = "#becab9"
FG_MUTED = "#889484"
FG_HEADER = "#e1e2eb"

# ─── Accent (DevForge emerald primary) ───────────────────────────────
ACCENT_PRIMARY = "#6fdd78"
ACCENT_SECONDARY = "#a2c9ff"
ACCENT_GRADIENT_START = "#6fdd78"
ACCENT_GRADIENT_END = "#34a547"
ACCENT_GLOW = "rgba(111, 221, 120, 0.25)"

# ─── Status colors ─────────────────────────────────────────────────
GREEN = "#6fdd78"
GREEN_DIM = "rgba(111, 221, 120, 0.15)"
GREEN_DARK = "#34a547"
RED = "#ffb4ab"
RED_DIM = "rgba(255, 180, 171, 0.15)"
AMBER = "#fbbf24"
CYAN = "#a2c9ff"
PURPLE = "#d5bbff"

# ─── Borders ────────────────────────────────────────────────────────
BORDER = "#3e4a3d"
BORDER_LIGHT = "#3e4a3d"
BORDER_ACCENT = "rgba(111, 221, 120, 0.30)"

# ─── Badges ─────────────────────────────────────────────────────────
BADGE_BG = "#191c22"
BADGE_GREEN_BG = "rgba(111, 221, 120, 0.15)"
BADGE_GREEN_FG = "#6fdd78"
BADGE_AMBER_BG = "rgba(251, 191, 36, 0.15)"
BADGE_AMBER_FG = "#fbbf24"
BADGE_ACCENT_BG = "rgba(111, 221, 120, 0.15)"
BADGE_ACCENT_FG = "#6fdd78"

# ─── Progress ───────────────────────────────────────────────────────
PROGRESS_BG = "#191c22"
PROGRESS_FG = "#6fdd78"

# ─── Scrollbar ──────────────────────────────────────────────────────
SCROLLBAR_BG = "transparent"
SCROLLBAR_FG = "#3e4a3d"

# ─── Column header ──────────────────────────────────────────────────
COLUMN_HEADER_FG = "#889484"

# ─── Sidebar ────────────────────────────────────────────────────────
SIDEBAR_ITEM_HOVER = "#272a31"
SIDEBAR_ITEM_ACTIVE = "#1d2026"
SIDEBAR_ICON_COLOR = "#889484"
SIDEBAR_ICON_ACTIVE = "#6fdd78"


def build_stylesheet() -> str:
    """Return the global QSS stylesheet for the application.

    Delegates to the Windows 11 Fluent Design theme. Legacy colour constants in
    this module are preserved for widgets that still import them directly.
    """
    from udm.gui.fluent import fluent_stylesheet

    return fluent_stylesheet()


def _legacy_stylesheet() -> str:
    """The DevForge dark stylesheet, kept for reference/fallback."""
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
            border: 1.5px solid {BORDER};
            border-radius: 4px;
            background-color: transparent;
        }}
        QCheckBox::indicator:checked {{
            background-color: {ACCENT_PRIMARY};
            border-color: {ACCENT_PRIMARY};
            image: none;
        }}
        QCheckBox::indicator:hover {{
            border-color: {ACCENT_PRIMARY};
        }}

        QTextEdit {{
            background-color: {BG_LOG};
            color: {FG_DIM};
            border: none;
            font-family: "JetBrains Mono", "Cascadia Code", "Consolas", monospace;
            font-size: 12px;
            padding: 14px;
            selection-background-color: rgba(111, 221, 120, 0.25);
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
