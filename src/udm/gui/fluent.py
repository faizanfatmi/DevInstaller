"""Windows 11 Fluent Design tokens and global stylesheet — monochrome dark variant."""

from __future__ import annotations

ACCENT           = "#ffffff"
ACCENT_HOVER     = "#e0e0e0"
ACCENT_PRESSED   = "#cccccc"
ACCENT_TEXT      = "#0d0d0d"
ACCENT_SUBTLE    = "rgba(255, 255, 255, 0.08)"

WINDOW_BASE      = "#0d0d0d"
LAYER            = "rgba(255, 255, 255, 0.04)"
LAYER_ALT        = "rgba(255, 255, 255, 0.02)"
SUBTLE_HOVER     = "rgba(255, 255, 255, 0.06)"
SUBTLE_PRESSED   = "rgba(255, 255, 255, 0.03)"
CONTROL_FILL     = "rgba(255, 255, 255, 0.05)"
CONTROL_HOVER    = "rgba(255, 255, 255, 0.08)"
CONTROL_INPUT    = "rgba(255, 255, 255, 0.04)"

TEXT_PRIMARY     = "#e8e8e8"
TEXT_SECONDARY   = "rgba(255, 255, 255, 0.65)"
TEXT_TERTIARY    = "rgba(255, 255, 255, 0.40)"
TEXT_DISABLED    = "rgba(255, 255, 255, 0.25)"

STROKE           = "rgba(255, 255, 255, 0.06)"
STROKE_STRONG    = "rgba(255, 255, 255, 0.10)"
CARD_STROKE      = "rgba(255, 255, 255, 0.05)"

SUCCESS          = "#4ade80"
WARNING          = "#fbbf24"
DANGER           = "#f87171"

RADIUS_CONTROL   = 4
RADIUS_CARD      = 8
SPACE_XS, SPACE_S, SPACE_M, SPACE_L, SPACE_XL = 4, 8, 12, 16, 24

FONT_STACK = (
    '"Segoe UI Variable Text", "Segoe UI Variable", "Segoe UI", '
    '"Inter", "SF Pro Text", -apple-system, sans-serif'
)
FONT_MONO = '"Cascadia Code", "Cascadia Mono", "JetBrains Mono", "Consolas", monospace'


def fluent_stylesheet() -> str:
    """Return the global Fluent QSS for the application."""
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
            border-bottom: 1px solid {STROKE_STRONG};
            border-radius: {RADIUS_CONTROL}px;
            padding: 9px 12px;
            selection-background-color: rgba(255, 255, 255, 0.20);
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
            background-color: #1a1a1a;
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
            background-color: #ffffff;
            border-radius: 2px;
        }}

        /* ── Checkbox — circular, flat, green when checked ── */
        QCheckBox {{ spacing: 8px; }}
        QCheckBox::indicator {{
            width: 20px; height: 20px;
            border: 1.5px solid #666666;
            border-radius: 10px;
            background-color: transparent;
        }}
        QCheckBox::indicator:hover {{
            border-color: #999999;
        }}
        QCheckBox::indicator:checked {{
            background-color: #22c55e;
            border-color: #22c55e;
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
        QMessageBox {{ background-color: #151515; }}
        QMessageBox QLabel {{ color: {TEXT_PRIMARY}; }}
        QMessageBox QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #4ade80, stop:0.5 #22c55e, stop:1 #16a34a);
            color: #ffffff;
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 10px;
            padding: 8px 24px;
            font-weight: 700;
        }}
        QMessageBox QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #86efac, stop:0.5 #4ade80, stop:1 #22c55e);
        }}

        /* ── Tooltip ── */
        QToolTip {{
            background-color: #1a1a1a;
            color: {TEXT_PRIMARY};
            border: 1px solid {STROKE_STRONG};
            border-radius: {RADIUS_CONTROL}px;
            padding: 6px 10px;
        }}
    """
