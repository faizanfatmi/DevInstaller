"""Scrollable tool list with monochrome dark card-style rows."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox, QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel,
    QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)
from PySide6.QtGui import QColor

from udm.gui.theme import (
    ACCENT_GLOW, ACCENT_PRIMARY, BADGE_BG, BG_CARD, BG_INPUT, BG_ROW,
    BG_ROW_HOVER, BG_ROW_SELECTED, BG_WINDOW, BORDER, BORDER_ACCENT,
    BORDER_LIGHT, COLUMN_HEADER_FG, FG, FG_DIM, FG_MUTED, GREEN,
)
from udm.gui.widgets import PillBadge

# Category color mapping — muted for dark theme
CATEGORY_COLORS = {
    "Languages": ("#a78bfa", "rgba(167, 139, 250, 0.10)"),
    "Compilers": ("#4ade80", "rgba(74, 222, 128, 0.10)"),
    "SDKs": ("#60a5fa", "rgba(96, 165, 250, 0.10)"),
    "Frameworks": ("#fb923c", "rgba(251, 146, 60, 0.10)"),
    "Databases": ("#22d3ee", "rgba(34, 211, 238, 0.10)"),
    "DevOps": ("#fbbf24", "rgba(251, 191, 36, 0.10)"),
    "Package Managers": ("#c4b5fd", "rgba(196, 181, 253, 0.10)"),
    "IDEs": ("#f472b6", "rgba(244, 114, 182, 0.10)"),
    "Editors": ("#34d399", "rgba(52, 211, 153, 0.10)"),
    "Version Control": ("#fca5a5", "rgba(252, 165, 165, 0.10)"),
    "Cloud": ("#93c5fd", "rgba(147, 197, 253, 0.10)"),
    "Mobile": ("#f87171", "rgba(248, 113, 113, 0.10)"),
    "Web Dev": ("#38bdf8", "rgba(56, 189, 248, 0.10)"),
    "AI/ML": ("#a78bfa", "rgba(167, 139, 250, 0.10)"),
    "Testing": ("#67e8f9", "rgba(103, 232, 249, 0.10)"),
    "Build Tools": ("#fde68a", "rgba(253, 230, 138, 0.10)"),
    "Containers": ("#60a5fa", "rgba(96, 165, 250, 0.10)"),
    "Terminal": ("#4ade80", "rgba(74, 222, 128, 0.10)"),
}


class ToolRow(QFrame):
    toggled = Signal(str, bool)

    def __init__(self, tool, parent=None):
        super().__init__(parent)
        self.tool = tool
        self.key = tool.get("key", tool["name"])
        self._selected = False
        self.setStyleSheet(f"ToolRow{{background-color:{BG_ROW};"
            f"border:1px solid {BORDER};border-radius:8px;}}")
        self.setFixedHeight(64)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(0)

        self.checkbox = QCheckBox()
        self.checkbox.setFixedWidth(36)
        self.checkbox.stateChanged.connect(self._on_check)
        layout.addWidget(self.checkbox)

        name_col = QVBoxLayout()
        name_col.setSpacing(3)
        name_col.setContentsMargins(0, 10, 0, 10)
        self.name_label = QLabel(tool.get("name", ""))
        self.name_label.setStyleSheet(f"color:{FG};font-size:13px;"
            "font-weight:600;background:transparent;")
        name_col.addWidget(self.name_label)
        desc_text = tool.get("description", "")
        if len(desc_text) > 80: desc_text = desc_text[:77] + "..."
        self.desc_label = QLabel(desc_text)
        self.desc_label.setStyleSheet(f"color:{FG_MUTED};font-size:11px;"
            "background:transparent;")
        name_col.addWidget(self.desc_label)
        name_widget = QWidget()
        name_widget.setLayout(name_col)
        name_widget.setStyleSheet("background:transparent;")
        name_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(name_widget, stretch=1)

        version = (tool.get("detect_cmd", "").split("--version")[0].strip()
            if "--version" in tool.get("detect_cmd", "") else "")
        version_text = "—"
        if version:
            version_text = version.split()[-1] if version.split() else "—"
        self.version_label = QLabel(version_text)
        self.version_label.setFixedWidth(100)
        self.version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.version_label.setStyleSheet(f"color:{FG_DIM};"
            'font-family:"Cascadia Code","Consolas",monospace;'
            "font-size:12px;background:transparent;")
        layout.addWidget(self.version_label)
        layout.addSpacing(12)

        cat = tool.get("category", "Other")
        cat_fg, cat_bg = CATEGORY_COLORS.get(cat, (FG_DIM, BADGE_BG))
        self.cat_badge = QLabel(cat.upper())
        self.cat_badge.setFixedWidth(130)
        self.cat_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cat_badge.setStyleSheet(f"QLabel{{background-color:transparent;"
            f"color:{cat_fg};border-radius:4px;padding:4px 10px;"
            "font-size:10px;font-weight:600;letter-spacing:0.5px;}}")
        layout.addWidget(self.cat_badge)

    def _on_check(self, state):
        self._selected = state == Qt.CheckState.Checked.value
        self._update_visual()
        self.toggled.emit(self.key, self._selected)

    def _update_visual(self):
        if self._selected:
            self.setStyleSheet(f"ToolRow{{background-color:{BG_ROW_SELECTED};"
                f"border:1px solid #ffffff;border-radius:8px;}}")
        else:
            self.setStyleSheet(f"ToolRow{{background-color:{BG_ROW};"
                f"border:1px solid {BORDER};border-radius:8px;}}")

    def is_checked(self): return self.checkbox.isChecked()
    def set_checked(self, checked): self.checkbox.setChecked(checked)

    def matches_filter(self, query, category):
        if category != "All" and self.tool.get("category", "") != category: return False
        if query:
            name = self.tool.get("name", "").lower()
            desc = self.tool.get("description", "").lower()
            key = self.key.lower()
            if query not in name and query not in desc and query not in key: return False
        return True

    def enterEvent(self, event):
        if not self._selected:
            self.setStyleSheet(f"ToolRow{{background-color:{BG_ROW_HOVER};"
                f"border:1px solid {BORDER_LIGHT};border-radius:8px;}}")
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._update_visual()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self.checkbox.setChecked(not self.checkbox.isChecked())
        super().mousePressEvent(event)


class ColumnHeader(QWidget):
    select_all_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(40)
        self.setStyleSheet(f"background-color:{BG_CARD};"
            f"border-bottom:1px solid {BORDER};"
            "border-top-left-radius:8px;border-top-right-radius:8px;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(0)
        self.select_all_cb = QCheckBox()
        self.select_all_cb.setFixedWidth(36)
        self.select_all_cb.stateChanged.connect(
            lambda state: self.select_all_changed.emit(state == Qt.CheckState.Checked.value))
        layout.addWidget(self.select_all_cb)
        hs = f"color:{COLUMN_HEADER_FG};font-size:11px;font-weight:600;" \
             "letter-spacing:1px;background:transparent;"
        name_header = QLabel("PACKAGE")
        name_header.setStyleSheet(hs)
        layout.addWidget(name_header, stretch=1)
        version_header = QLabel("VERSION")
        version_header.setFixedWidth(100)
        version_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_header.setStyleSheet(hs)
        layout.addWidget(version_header)
        layout.addSpacing(12)
        cat_header = QLabel("CATEGORY")
        cat_header.setFixedWidth(130)
        cat_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cat_header.setStyleSheet(hs)
        layout.addWidget(cat_header)


class ToolTable(QWidget):
    selection_changed = Signal(int)

    def __init__(self, tools, parent=None):
        super().__init__(parent)
        self._rows = []
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(24, 8, 24, 0)
        outer_layout.setSpacing(0)
        self.column_header = ColumnHeader()
        self.column_header.select_all_changed.connect(self._on_select_all)
        outer_layout.addWidget(self.column_header)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet(f"QScrollArea{{border:none;"
            f"background-color:{BG_CARD};"
            "border-bottom-left-radius:8px;border-bottom-right-radius:8px;}}")
        self.list_widget = QWidget()
        self.list_widget.setStyleSheet(f"background-color:{BG_CARD};")
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setContentsMargins(12, 12, 12, 12)
        self.list_layout.setSpacing(10)
        self._populate(tools)
        self.list_layout.addStretch()
        self.scroll_area.setWidget(self.list_widget)
        outer_layout.addWidget(self.scroll_area)

    def _populate(self, tools):
        for tool in tools:
            row = ToolRow(tool)
            row.toggled.connect(self._on_row_toggled)
            self._rows.append(row)
            self.list_layout.addWidget(row)

    def _on_row_toggled(self, key, checked):
        self.selection_changed.emit(sum(1 for r in self._rows if r.is_checked()))

    def _on_select_all(self, checked):
        for row in self._rows:
            if row.isVisible(): row.set_checked(checked)

    def apply_filter(self, query, category):
        for row in self._rows: row.setVisible(row.matches_filter(query, category))

    def selected_tools(self): return [r.tool for r in self._rows if r.is_checked()]
    def selected_count(self): return sum(1 for r in self._rows if r.is_checked())

    def clear_selection(self):
        self.column_header.select_all_cb.setChecked(False)
        for row in self._rows: row.set_checked(False)

    def select_tools_by_keys(self, keys):
        key_set = set(keys)
        first_matched_row = None
        for row in self._rows:
            should_check = row.key in key_set
            row.set_checked(should_check)
            row.setVisible(should_check)
            if should_check and first_matched_row is None:
                first_matched_row = row
        self.selection_changed.emit(sum(1 for r in self._rows if r.is_checked()))
        if first_matched_row is not None:
            from PySide6.QtCore import QTimer
            QTimer.singleShot(100, lambda: self.scroll_area.ensureWidgetVisible(
                first_matched_row, 0, 50))

    def rebuild(self, tools):
        for row in self._rows:
            self.list_layout.removeWidget(row)
            row.deleteLater()
        self._rows.clear()
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        self._populate(tools)
        self.list_layout.addStretch()
        self.selection_changed.emit(0)
