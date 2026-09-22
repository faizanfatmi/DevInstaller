"""Windows 11 Fluent Design tokens and global stylesheet — DevForge Dark variant."""

from __future__ import annotations

ACCENT           = "#6fdd78"
ACCENT_HOVER     = "#8bfb91"
ACCENT_PRESSED   = "#34a547"
ACCENT_TEXT      = "#00390e"
ACCENT_SUBTLE    = "rgba(111, 221, 120, 0.15)"

WINDOW_BASE      = "#101319"
LAYER            = "rgba(255, 255, 255, 0.03)"
LAYER_ALT        = "#0b0e14"
SUBTLE_HOVER     = "rgba(255, 255, 255, 0.05)"
SUBTLE_PRESSED   = "rgba(255, 255, 255, 0.03)"
CONTROL_FILL     = "#191c22"
CONTROL_HOVER    = "#272a31"
CONTROL_INPUT    = "#191c22"

TEXT_PRIMARY     = "#e1e2eb"
TEXT_SECONDARY   = "#becab9"
TEXT_TERTIARY    = "#889484"
TEXT_DISABLED    = "rgba(255, 255, 255, 0.20)"

STROKE           = "#3e4a3d"
STROKE_STRONG    = "#32353c"
CARD_STROKE      = "rgba(62, 74, 61, 0.80)"

SUCCESS          = "#6fdd78"
WARNING          = "#fbbf24"
DANGER           = "#ffb4ab"

RADIUS_CONTROL   = 6
RADIUS_CARD      = 8
SPACE_XS, SPACE_S, SPACE_M, SPACE_L, SPACE_XL = 4, 8, 12, 16, 24

FONT_STACK = (
    '"Segoe UI Variable Text", "Segoe UI Variable", "Segoe UI", '
    '"Inter", "SF Pro Text", -apple-system, sans-serif'
)
FONT_MONO = '"Cascadia Code", "Cascadia Mono", "JetBrains Mono", "Consolas", monospace'


def fluent_stylesheet() -> str:
    """Return the global Fluent QSS for the application — DevForge Dark variant."""
    return f"""
        * {{
            font-family: {FONT_STACK};
            font-size: 14px;
            color: {TEXT_PRIMARY};
        }}
        QMainWindow, QDialog {{
            background-color: {WINDOW_BASE};
        }}
        QWidget {{
            color: {TEXT_PRIMARY};
        }}
        QLabel {{ background: transparent; }}

        /* ── Text inputs ── */
        QLineEdit {{
            background-color: {CONTROL_INPUT};
            color: {TEXT_PRIMARY};
            border: 1px solid {STROKE};
            border-radius: {RADIUS_CONTROL}px;
            padding: 9px 12px;
            selection-background-color: rgba(111, 221, 120, 0.30);
        }}
        QLineEdit:hover {{ background-color: {CONTROL_HOVER}; }}
        QLineEdit:focus {{
            background-color: {WINDOW_BASE};
            border: 1px solid {STROKE};
            border-bottom: 2px solid {ACCENT};
        }}
        QLineEdit:disabled {{ color: {TEXT_DISABLED}; }}

        /* ── Combo box ── */
        QComboBox {{
            background-color: {CONTROL_FILL};
            color: {TEXT_PRIMARY};
            border: 1px solid {STROKE};
            border-radius: {RADIUS_CONTROL}px;
            padding: 7px 12px;
            min-width: 80px;
        }}
        QComboBox:hover {{ background-color: {CONTROL_HOVER}; }}
        QComboBox::drop-down {{ border: none; width: 28px; }}
        QComboBox::down-arrow {{
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid {TEXT_SECONDARY};
            margin-right: 12px;
        }}
        QComboBox QAbstractItemView {{
            background-color: #191c22;
            color: {TEXT_PRIMARY};
            border: 1px solid {STROKE_STRONG};
            border-radius: {RADIUS_CARD}px;
            selection-background-color: {ACCENT_SUBTLE};
            selection-color: {TEXT_PRIMARY};
            outline: none;
            padding: 4px;
        }}

        /* ── Buttons ── */
        QPushButton {{
            background-color: {CONTROL_FILL};
            color: {TEXT_PRIMARY};
            border: 1px solid {STROKE};
            border-radius: {RADIUS_CONTROL}px;
            padding: 8px 20px;
            font-weight: 600;
        }}
        QPushButton:hover {{ background-color: {CONTROL_HOVER}; }}
        QPushButton:pressed {{ background-color: {SUBTLE_PRESSED}; color: {TEXT_SECONDARY}; }}
        QPushButton:disabled {{ color: {TEXT_DISABLED}; border-color: {STROKE}; }}

        /* ── Scrollbars ── */
        QScrollBar:vertical {{
            background: transparent;
            width: 8px;
            margin: 2px;
        }}
        QScrollBar::handle:vertical {{
            background: {STROKE_STRONG};
            border-radius: 3px;
            min-height: 40px;
        }}
        QScrollBar::handle:vertical:hover {{ background: {TEXT_TERTIARY}; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}

        /* ── Progress bar ── */
        QProgressBar {{
            background-color: {CONTROL_FILL};
            border: none;
            border-radius: 2px;
            text-align: center;
            color: transparent;
            max-height: 3px;
        }}
        QProgressBar::chunk {{
            background-color: {ACCENT};
            border-radius: 2px;
        }}

        /* ── Checkbox — rounded square, emerald when checked ── */
        QCheckBox {{ spacing: 8px; }}
        QCheckBox::indicator {{
            width: 18px; height: 18px;
            border: 1.5px solid #484F58;
            border-radius: 4px;
            background-color: transparent;
        }}
        QCheckBox::indicator:hover {{
            border-color: {ACCENT_HOVER};
        }}
        QCheckBox::indicator:checked {{
            background-color: {ACCENT};
            border-color: {ACCENT};
        }}

        /* ── Text edit / log ── */
        QTextEdit {{
            background-color: {LAYER_ALT};
            color: {TEXT_SECONDARY};
            border: none;
            font-family: {FONT_MONO};
            font-size: 12px;
            padding: 12px;
            selection-background-color: {ACCENT_SUBTLE};
        }}

        /* ── Message / dialog ── */
        QMessageBox {{ background-color: #191c22; }}
        QMessageBox QLabel {{ color: {TEXT_PRIMARY}; }}
        QMessageBox QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #8bfb91, stop:0.5 #6fdd78, stop:1 #34a547);
            color: #00390e;
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 8px;
            padding: 8px 24px;
            font-weight: 700;
        }}
        QMessageBox QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #a6fca9, stop:0.5 #8bfb91, stop:1 #6fdd78);
        }}

        /* ── Tooltip ── */
        QToolTip {{
            background-color: #191c22;
            color: {TEXT_PRIMARY};
            border: 1px solid {STROKE_STRONG};
            border-radius: {RADIUS_CONTROL}px;
            padding: 6px 10px;
        }}
    """
