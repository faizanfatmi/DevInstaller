"""Windows 11 Fluent Design tokens and global stylesheet.

This module centralises the Fluent design language for DevInstaller: an accent
ramp, neutral surface layers suitable for a Mica/Acrylic backdrop, elevation
borders, corner radii, a Segoe UI Variable typography stack, and a spacing
scale. ``fluent_stylesheet()`` returns a complete QSS covering the common Qt
controls with correct hover / pressed / disabled states.

Colours are kept close to the Windows 11 system palette so the app blends with
the OS. The surfaces use partial transparency where a Mica backdrop is active
(see :mod:`udm.gui.mica`).
"""

from __future__ import annotations

# ── Accent ramp (Windows 11 default blue) ────────────────────────────
ACCENT           = "#0067c0"
ACCENT_HOVER     = "#1975c5"
ACCENT_PRESSED   = "#3183cb"
ACCENT_TEXT      = "#ffffff"
ACCENT_SUBTLE    = "rgba(0, 103, 192, 0.10)"

# ── Neutral surfaces (dark theme, Mica-friendly) ───────────────────────
WINDOW_BASE      = "#202020"   # solid fallback when Mica is unavailable
LAYER            = "rgba(255, 255, 255, 0.05)"   # card / layer fill
LAYER_ALT        = "rgba(255, 255, 255, 0.03)"
SUBTLE_HOVER     = "rgba(255, 255, 255, 0.08)"
SUBTLE_PRESSED   = "rgba(255, 255, 255, 0.04)"
CONTROL_FILL     = "rgba(255, 255, 255, 0.06)"
CONTROL_HOVER    = "rgba(255, 255, 255, 0.09)"
CONTROL_INPUT    = "rgba(255, 255, 255, 0.05)"

# ── Text ────────────────────────────────────────────────
TEXT_PRIMARY     = "#ffffff"
TEXT_SECONDARY   = "rgba(255, 255, 255, 0.79)"
TEXT_TERTIARY    = "rgba(255, 255, 255, 0.55)"
TEXT_DISABLED    = "rgba(255, 255, 255, 0.36)"

# ── Strokes / borders ───────────────────────────────────────
STROKE           = "rgba(255, 255, 255, 0.09)"
STROKE_STRONG    = "rgba(255, 255, 255, 0.16)"
CARD_STROKE      = "rgba(255, 255, 255, 0.07)"

# ── Status ─────────────────────────────────────────────
SUCCESS          = "#6ccb5f"
WARNING          = "#fce100"
DANGER           = "#ff99a4"

# ── Radii (Fluent uses 4/8 for controls and cards) ────────────────────
RADIUS_CONTROL   = 4
RADIUS_CARD      = 8

# ── Spacing scale (px) ──────────────────────────────────────
SPACE_XS, SPACE_S, SPACE_M, SPACE_L, SPACE_XL = 4, 8, 12, 16, 24

# ── Typography ───────────────────────────────────────────
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
            selection-background-color: {ACCENT};
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
            background-color: #2c2c2c;
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
        QPushButton:default {{
            background-color: {ACCENT};
            color: {ACCENT_TEXT};
            border: 1px solid {ACCENT};
        }}
        QPushButton:default:hover {{ background-color: {ACCENT_HOVER}; }}
        QPushButton:default:pressed {{ background-color: {ACCENT_PRESSED}; }}

        /* ── Scrollbars ── */
        QScrollBar:vertical {{
            background: transparent;
            width: 12px;
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
            border-radius: 3px;
            text-align: center;
            color: transparent;
            max-height: 4px;
        }}
        QProgressBar::chunk {{
            background-color: {ACCENT};
            border-radius: 3px;
        }}

        /* ── Checkbox ── */
        QCheckBox {{ spacing: 8px; }}
        QCheckBox::indicator {{
            width: 18px; height: 18px;
            border: 1px solid {STROKE_STRONG};
            border-radius: {RADIUS_CONTROL}px;
            background-color: {CONTROL_INPUT};
        }}
        QCheckBox::indicator:hover {{ border-color: {TEXT_TERTIARY}; }}
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

        /* ── Message / dialog buttons ── */
        QMessageBox {{ background-color: {WINDOW_BASE}; }}
        QMessageBox QLabel {{ color: {TEXT_PRIMARY}; }}

        /* ── Tooltip ── */
        QToolTip {{
            background-color: #2c2c2c;
            color: {TEXT_PRIMARY};
            border: 1px solid {STROKE_STRONG};
            border-radius: {RADIUS_CONTROL}px;
            padding: 6px 10px;
        }}
    """
