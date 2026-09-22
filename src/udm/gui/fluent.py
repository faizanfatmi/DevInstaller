"""Windows 11 Fluent Design tokens and global stylesheet — deep navy dark variant."""

from __future__ import annotations

ACCENT           = "#3b82f6"
ACCENT_HOVER     = "#60a5fa"
ACCENT_PRESSED   = "#2563eb"
ACCENT_TEXT      = "#ffffff"
ACCENT_SUBTLE    = "rgba(59, 130, 246, 0.12)"

WINDOW_BASE      = "#0c1222"
LAYER            = "rgba(255, 255, 255, 0.03)"
LAYER_ALT        = "rgba(255, 255, 255, 0.02)"
SUBTLE_HOVER     = "rgba(255, 255, 255, 0.05)"
SUBTLE_PRESSED   = "rgba(255, 255, 255, 0.03)"
CONTROL_FILL     = "rgba(255, 255, 255, 0.05)"
CONTROL_HOVER    = "rgba(255, 255, 255, 0.08)"
CONTROL_INPUT    = "#162035"

TEXT_PRIMARY     = "#e2e8f0"
TEXT_SECONDARY   = "rgba(148, 163, 184, 1.0)"
TEXT_TERTIARY    = "rgba(71, 85, 105, 1.0)"
TEXT_DISABLED    = "rgba(255, 255, 255, 0.20)"

STROKE           = "rgba(30, 45, 74, 1.0)"
STROKE_STRONG    = "rgba(42, 63, 95, 1.0)"
CARD_STROKE      = "rgba(30, 45, 74, 0.80)"

SUCCESS          = "#4ade80"
WARNING          = "#fbbf24"
DANGER           = "#f87171"

RADIUS_CONTROL   = 6
RADIUS_CARD      = 8
SPACE_XS, SPACE_S, SPACE_M, SPACE_L, SPACE_XL = 4, 8, 12, 16, 24

FONT_STACK = (
    '"Segoe UI Variable Text", "Segoe UI Variable", "Segoe UI", '
    '"Inter", "SF Pro Text", -apple-system, sans-serif'
)
FONT_MONO = '"Cascadia Code", "Cascadia Mono", "JetBrains Mono", "Consolas", monospace'


def fluent_stylesheet() -> str:
    """Return the global Fluent QSS for the application — deep navy variant."""
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
            selection-background-color: rgba(59, 130, 246, 0.30);
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
            background-color: #111a2e;
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

        /* ── Checkbox — rounded square, blue when checked ── */
        QCheckBox {{ spacing: 8px; }}
        QCheckBox::indicator {{
            width: 18px; height: 18px;
            border: 1.5px solid #475569;
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
        QMessageBox {{ background-color: #111a2e; }}
        QMessageBox QLabel {{ color: {TEXT_PRIMARY}; }}
        QMessageBox QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #60a5fa, stop:0.5 #3b82f6, stop:1 #2563eb);
            color: #ffffff;
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 8px;
            padding: 8px 24px;
            font-weight: 700;
        }}
        QMessageBox QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #93bbfd, stop:0.5 #60a5fa, stop:1 #3b82f6);
        }}

        /* ── Tooltip ── */
        QToolTip {{
            background-color: #111a2e;
            color: {TEXT_PRIMARY};
            border: 1px solid {STROKE_STRONG};
            border-radius: {RADIUS_CONTROL}px;
            padding: 6px 10px;
        }}
    """
