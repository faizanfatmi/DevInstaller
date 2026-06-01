"""Search bar — floating search input with AI Stack toggle and tool count badge."""

from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
    QGraphicsDropShadowEffect,
    QSizePolicy,
)
from PySide6.QtGui import QColor

from udm.gui.theme import (
    ACCENT_PRIMARY,
    ACCENT_GRADIENT_START,
    ACCENT_GRADIENT_END,
    ACCENT_GLOW,
    BG_CARD,
    BG_INPUT,
    BG_ROW_HOVER,
    BADGE_ACCENT_BG,
    BADGE_ACCENT_FG,
    BORDER,
    BORDER_ACCENT,
    FG,
    FG_DIM,
    FG_MUTED,
    GREEN,
    PURPLE,
)
from udm.gui.widgets import ActionButton


class StackChip(QLabel):
    """Small rounded chip showing a detected tool name."""

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(f"""
            QLabel {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(108, 92, 231, 0.18), stop:1 rgba(0, 180, 216, 0.18));
                color: #b388ff;
                border: 1px solid rgba(108, 92, 231, 0.30);
                border-radius: 10px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 0.3px;
            }}
        """)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)


class ChipBar(QWidget):
    """Horizontal scrollable bar showing detected tool chips."""

    clear_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self.setVisible(False)

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(24, 0, 24, 4)
        self._layout.setSpacing(6)

        # Stack name label
        self._stack_label = QLabel()
        self._stack_label.setStyleSheet(f"""
            color: {ACCENT_PRIMARY};
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.8px;
            background: transparent;
        """)
        self._layout.addWidget(self._stack_label)

        # Chips container
        self._chips_container = QWidget()
        self._chips_container.setStyleSheet("background: transparent;")
        self._chips_layout = QHBoxLayout(self._chips_container)
        self._chips_layout.setContentsMargins(0, 0, 0, 0)
        self._chips_layout.setSpacing(6)
        self._layout.addWidget(self._chips_container, stretch=1)

        # Clear button
        self._clear_btn = QLabel("✕ Clear")
        self._clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._clear_btn.setStyleSheet(f"""
            QLabel {{
                color: {FG_MUTED};
                font-size: 11px;
                font-weight: 600;
                padding: 4px 8px;
                background: transparent;
            }}
            QLabel:hover {{
                color: {FG};
            }}
        """)
        self._clear_btn.mousePressEvent = lambda _: self.clear_requested.emit()
        self._layout.addWidget(self._clear_btn)

    def show_results(self, stack_name: str | None, display_names: dict[str, str]):
        """Populate chips from parse results."""
        # Clear previous chips
        while self._chips_layout.count():
            item = self._chips_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if stack_name:
            self._stack_label.setText(f"🎯 {stack_name.upper()} STACK →")
            self._stack_label.setVisible(True)
        else:
            self._stack_label.setText("🔍 DETECTED →")
            self._stack_label.setVisible(True)

        for key, name in display_names.items():
            chip = StackChip(name)
            self._chips_layout.addWidget(chip)

        self._chips_layout.addStretch()
        self.setVisible(True)

    def clear_chips(self):
        """Remove all chips and hide the bar."""
        while self._chips_layout.count():
            item = self._chips_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._stack_label.setText("")
        self.setVisible(False)


class SearchBar(QWidget):
    """Search input with AI Stack toggle and refresh button."""

    filter_changed = Signal()
    refresh_requested = Signal()
    ai_select_requested = Signal(list)  # emits list of tool keys
    ai_clear_requested = Signal()

    def __init__(self, categories: list[str], parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self._ai_mode = False

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # ── Top row: search + buttons ──────────────────────────────
        top_row = QWidget()
        top_row.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(top_row)
        layout.setContentsMargins(24, 16, 24, 8)
        layout.setSpacing(12)

        # AI toggle button
        self.ai_toggle = _AIToggleButton()
        self.ai_toggle.clicked.connect(self._toggle_ai_mode)
        layout.addWidget(self.ai_toggle)

        # Search input with custom styling
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍  Search packages...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._on_text_changed)
        self.search_input.returnPressed.connect(self._on_enter_pressed)
        self._apply_input_style(ai_active=False)
        layout.addWidget(self.search_input, stretch=1)

        # Refresh button
        refresh_btn = ActionButton("↻  Refresh", "secondary")
        refresh_btn.clicked.connect(self.refresh_requested.emit)
        layout.addWidget(refresh_btn)

        outer_layout.addWidget(top_row)

        # ── Chip bar (shown when AI returns results) ───────────────
        self.chip_bar = ChipBar()
        self.chip_bar.clear_requested.connect(self._on_chip_clear)
        outer_layout.addWidget(self.chip_bar)

    # ── Public API ──────────────────────────────────────────────────

    def search_text(self) -> str:
        if self._ai_mode:
            return ""  # In AI mode, filtering is done via selection, not text
        return self.search_input.text().strip().lower()

    def selected_category(self) -> str:
        """Category now comes from sidebar; this returns 'All' for compat."""
        return getattr(self, "_current_category", "All")

    def set_category(self, category: str):
        """Set current category from sidebar."""
        self._current_category = category
        self.filter_changed.emit()

    def set_categories(self, categories: list[str]):
        """Compatibility method — categories are now in sidebar."""
        pass

    def is_ai_mode(self) -> bool:
        return self._ai_mode

    # ── Private ─────────────────────────────────────────────────────

    def _toggle_ai_mode(self):
        self._ai_mode = not self._ai_mode
        self.ai_toggle.set_active(self._ai_mode)
        self._apply_input_style(ai_active=self._ai_mode)

        if self._ai_mode:
            self.search_input.setPlaceholderText(
                "🤖  Describe your project… e.g. 'MERN stack banao'"
            )
            self.search_input.clear()
        else:
            self.search_input.setPlaceholderText("🔍  Search packages...")
            self.search_input.clear()
            self.chip_bar.clear_chips()
            self.ai_clear_requested.emit()
            self.filter_changed.emit()

    def _apply_input_style(self, ai_active: bool):
        if ai_active:
            border_color = ACCENT_PRIMARY
            focus_border = "#b388ff"
            bg = "#1a1530"
            focus_bg = "#1e1838"
        else:
            border_color = BORDER
            focus_border = ACCENT_PRIMARY
            bg = BG_INPUT
            focus_bg = "#1a1f30"

        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {bg};
                color: {FG};
                border: 1px solid {border_color};
                border-radius: 12px;
                padding: 12px 18px;
                font-size: 14px;
                selection-background-color: {ACCENT_PRIMARY};
            }}
            QLineEdit:focus {{
                border-color: {focus_border};
                background-color: {focus_bg};
            }}
        """)

    def _on_text_changed(self, text: str):
        if not self._ai_mode:
            self.filter_changed.emit()

    def _on_enter_pressed(self):
        if self._ai_mode:
            prompt = self.search_input.text().strip()
            if prompt:
                self._run_stack_parse(prompt)

    def _run_stack_parse(self, prompt: str):
        """Parse the prompt and emit results."""
        from udm.stack_parser import parse_prompt

        # We need access to the tools list — it's set by MainWindow
        tools = getattr(self, "_all_tools", None)
        result = parse_prompt(prompt, tools)

        if result.has_results:
            self.chip_bar.show_results(result.label, result.display_names)
            self.ai_select_requested.emit(result.matched_keys)
        else:
            self.chip_bar.clear_chips()
            # Show "no results" feedback in the chip bar
            self.chip_bar._stack_label.setText("❌  No matching tools found. Try another prompt.")
            self.chip_bar._stack_label.setStyleSheet(f"""
                color: #ff5252;
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 0.4px;
                background: transparent;
            """)
            self.chip_bar.setVisible(True)

    def _on_chip_clear(self):
        self.chip_bar.clear_chips()
        self.search_input.clear()
        self.ai_clear_requested.emit()

    def set_tools(self, tools: list[dict]):
        """Provide the full tools list for the parser to validate keys."""
        self._all_tools = tools


class _AIToggleButton(QWidget):
    """Custom toggle button for AI Stack mode with glow effect."""

    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._active = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(100, 42)

        self._label = QLabel("🤖 AI Stack", self)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setGeometry(0, 0, 100, 42)
        self._apply_style()

    def set_active(self, active: bool):
        self._active = active
        self._apply_style()

    def _apply_style(self):
        if self._active:
            self._label.setStyleSheet(f"""
                QLabel {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {ACCENT_GRADIENT_START}, stop:1 {ACCENT_GRADIENT_END});
                    color: #ffffff;
                    border: none;
                    border-radius: 12px;
                    padding: 0px;
                    font-size: 12px;
                    font-weight: 700;
                    letter-spacing: 0.5px;
                }}
            """)
            # Add glow effect
            glow = QGraphicsDropShadowEffect(self)
            glow.setBlurRadius(20)
            glow.setColor(QColor(108, 92, 231, 100))
            glow.setOffset(0, 0)
            self.setGraphicsEffect(glow)
        else:
            self._label.setStyleSheet(f"""
                QLabel {{
                    background-color: {BG_INPUT};
                    color: {FG_DIM};
                    border: 1.5px solid {BORDER};
                    border-radius: 12px;
                    padding: 0px;
                    font-size: 12px;
                    font-weight: 600;
                    letter-spacing: 0.5px;
                }}
            """)
            self.setGraphicsEffect(None)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)

    def enterEvent(self, event):
        if not self._active:
            self._label.setStyleSheet(f"""
                QLabel {{
                    background-color: {BG_ROW_HOVER};
                    color: {FG};
                    border: 1.5px solid {ACCENT_PRIMARY};
                    border-radius: 12px;
                    padding: 0px;
                    font-size: 12px;
                    font-weight: 600;
                    letter-spacing: 0.5px;
                }}
            """)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._apply_style()
        super().leaveEvent(event)
