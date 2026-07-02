"""Search bar — floating search input with AI Stack toggle and tool count badge."""

from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QLineEdit, QVBoxLayout, QWidget,
    QGraphicsDropShadowEffect, QSizePolicy,
)
from PySide6.QtGui import QColor

from udm.gui.theme import (
    ACCENT_PRIMARY, BG_CARD, BG_INPUT, BG_ROW_HOVER, BADGE_ACCENT_BG,
    BADGE_ACCENT_FG, BORDER, BORDER_ACCENT, FG, FG_DIM, FG_MUTED, GREEN, PURPLE,
)
from udm.gui.widgets import ActionButton


class StackChip(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("QLabel{background:rgba(255,255,255,0.06);color:#ccc;"
            "border:1px solid rgba(255,255,255,0.10);border-radius:4px;"
            "padding:4px 10px;font-size:11px;font-weight:500;}")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)


class ChipBar(QWidget):
    clear_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background:transparent;")
        self.setVisible(False)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(24, 0, 24, 4)
        self._layout.setSpacing(6)
        self._stack_label = QLabel()
        self._stack_label.setStyleSheet("color:#fff;font-size:11px;font-weight:600;"
            "letter-spacing:0.8px;background:transparent;")
        self._layout.addWidget(self._stack_label)
        self._chips_container = QWidget()
        self._chips_container.setStyleSheet("background:transparent;")
        self._chips_layout = QHBoxLayout(self._chips_container)
        self._chips_layout.setContentsMargins(0, 0, 0, 0)
        self._chips_layout.setSpacing(6)
        self._layout.addWidget(self._chips_container, stretch=1)
        self._clear_btn = QLabel("✕ Clear")
        self._clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._clear_btn.setStyleSheet(f"QLabel{{color:{FG_MUTED};font-size:11px;"
            f"font-weight:500;padding:4px 8px;background:transparent;}}")
        self._clear_btn.mousePressEvent = lambda _: self.clear_requested.emit()
        self._layout.addWidget(self._clear_btn)

    def show_results(self, stack_name, display_names):
        while self._chips_layout.count():
            item = self._chips_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        if stack_name:
            self._stack_label.setText(f"▸ {stack_name.upper()} STACK →")
        else:
            self._stack_label.setText("▸ DETECTED →")
        self._stack_label.setVisible(True)
        for key, name in display_names.items():
            self._chips_layout.addWidget(StackChip(name))
        self._chips_layout.addStretch()
        self.setVisible(True)

    def clear_chips(self):
        while self._chips_layout.count():
            item = self._chips_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        self._stack_label.setText("")
        self.setVisible(False)


class SearchBar(QWidget):
    filter_changed = Signal()
    refresh_requested = Signal()
    ai_select_requested = Signal(list)
    ai_clear_requested = Signal()

    def __init__(self, categories, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background:transparent;")
        self._ai_mode = False
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)
        top_row = QWidget()
        top_row.setStyleSheet("background:transparent;")
        layout = QHBoxLayout(top_row)
        layout.setContentsMargins(24, 14, 24, 8)
        layout.setSpacing(10)
        self.ai_toggle = _AIToggleButton()
        self.ai_toggle.clicked.connect(self._toggle_ai_mode)
        layout.addWidget(self.ai_toggle)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search packages...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._on_text_changed)
        self.search_input.returnPressed.connect(self._on_enter_pressed)
        self._apply_input_style(ai_active=False)
        layout.addWidget(self.search_input, stretch=1)
        refresh_btn = ActionButton("Refresh", "secondary")
        refresh_btn.clicked.connect(self.refresh_requested.emit)
        layout.addWidget(refresh_btn)
        outer_layout.addWidget(top_row)
        self.chip_bar = ChipBar()
        self.chip_bar.clear_requested.connect(self._on_chip_clear)
        outer_layout.addWidget(self.chip_bar)

    def search_text(self):
        if self._ai_mode: return ""
        return self.search_input.text().strip().lower()

    def selected_category(self):
        return getattr(self, "_current_category", "All")

    def set_category(self, category):
        self._current_category = category
        self.filter_changed.emit()

    def set_categories(self, categories): pass

    def is_ai_mode(self): return self._ai_mode

    def _toggle_ai_mode(self):
        self._ai_mode = not self._ai_mode
        self.ai_toggle.set_active(self._ai_mode)
        self._apply_input_style(ai_active=self._ai_mode)
        if self._ai_mode:
            self.search_input.setPlaceholderText("Describe your project…")
            self.search_input.clear()
        else:
            self.search_input.setPlaceholderText("Search packages...")
            self.search_input.clear()
            self.chip_bar.clear_chips()
            self.ai_clear_requested.emit()
            self.filter_changed.emit()

    def _apply_input_style(self, ai_active):
        if ai_active:
            bc, fbc, bg, fbg = "#ffffff", "#cccccc", "#1a1a1a", "#1f1f1f"
        else:
            bc, fbc, bg, fbg = "#1f1f1f", "#2a2a2a", BG_INPUT, "#1f1f1f"
        self.search_input.setStyleSheet(
            f"QLineEdit{{background-color:{bg};color:{FG};border:1px solid {bc};"
            f"border-radius:6px;padding:10px 16px;font-size:13px;"
            f"selection-background-color:rgba(255,255,255,0.20);}}"
            f"QLineEdit:focus{{border-color:{fbc};background-color:{fbg};}}")

    def _on_text_changed(self, text):
        if not self._ai_mode: self.filter_changed.emit()

    def _on_enter_pressed(self):
        if self._ai_mode:
            prompt = self.search_input.text().strip()
            if prompt: self._run_stack_parse(prompt)

    def _run_stack_parse(self, prompt):
        from udm.stack_parser import parse_prompt
        tools = getattr(self, "_all_tools", None)
        result = parse_prompt(prompt, tools)
        if result.has_results:
            self.chip_bar.show_results(result.label, result.display_names)
            self.ai_select_requested.emit(result.matched_keys)
        else:
            self.chip_bar.clear_chips()
            self.chip_bar._stack_label.setText("No matching tools found.")
            self.chip_bar._stack_label.setStyleSheet(
                "color:#f87171;font-size:11px;font-weight:500;background:transparent;")
            self.chip_bar.setVisible(True)

    def _on_chip_clear(self):
        self.chip_bar.clear_chips()
        self.search_input.clear()
        self.ai_clear_requested.emit()

    def set_tools(self, tools):
        self._all_tools = tools


class _AIToggleButton(QWidget):
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._active = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(90, 38)
        self._label = QLabel("AI Stack", self)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setGeometry(0, 0, 90, 38)
        self._apply_style()

    def set_active(self, active):
        self._active = active
        self._apply_style()

    def _apply_style(self):
        if self._active:
            self._label.setStyleSheet(
                "QLabel{background-color:#ffffff;color:#0d0d0d;border:none;"
                "border-radius:6px;font-size:12px;font-weight:700;}")
        else:
            self._label.setStyleSheet(
                f"QLabel{{background-color:{BG_INPUT};color:{FG_DIM};"
                "border:1px solid #1f1f1f;border-radius:6px;"
                "font-size:12px;font-weight:500;}}")
        self.setGraphicsEffect(None)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)

    def enterEvent(self, event):
        if not self._active:
            self._label.setStyleSheet(
                f"QLabel{{background-color:#222222;color:{FG};"
                "border:1px solid #2a2a2a;border-radius:6px;"
                "font-size:12px;font-weight:500;}}")
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._apply_style()
        super().leaveEvent(event)
