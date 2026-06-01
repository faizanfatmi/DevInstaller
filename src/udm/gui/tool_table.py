"""Scrollable tool list with premium card-style rows."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtGui import QColor

from udm.gui.theme import (
    ACCENT_GLOW,
    ACCENT_PRIMARY,
    BADGE_BG,
    BG_CARD,
    BG_INPUT,
    BG_ROW,
    BG_ROW_HOVER,
    BG_ROW_SELECTED,
    BG_WINDOW,
    BORDER,
    BORDER_ACCENT,
    COLUMN_HEADER_FG,
    FG,
    FG_DIM,
    FG_MUTED,
    GREEN,
)
from udm.gui.widgets import PillBadge

# Category color mapping for visual variety
CATEGORY_COLORS = {
    "Languages": ("#6c5ce7", "rgba(108, 92, 231, 0.12)"),
    "Compilers": ("#00b894", "rgba(0, 184, 148, 0.12)"),
    "SDKs": ("#0984e3", "rgba(9, 132, 227, 0.12)"),
    "Frameworks": ("#e17055", "rgba(225, 112, 85, 0.12)"),
    "Databases": ("#00cec9", "rgba(0, 206, 201, 0.12)"),
    "DevOps": ("#fdcb6e", "rgba(253, 203, 110, 0.12)"),
    "Package Managers": ("#a29bfe", "rgba(162, 155, 254, 0.12)"),
    "IDEs": ("#fd79a8", "rgba(253, 121, 168, 0.12)"),
    "Editors": ("#55efc4", "rgba(85, 239, 196, 0.12)"),
    "Version Control": ("#fab1a0", "rgba(250, 177, 160, 0.12)"),
    "Cloud": ("#74b9ff", "rgba(116, 185, 255, 0.12)"),
    "Mobile": ("#ff7675", "rgba(255, 118, 117, 0.12)"),
    "Web Dev": ("#00b4d8", "rgba(0, 180, 216, 0.12)"),
    "AI/ML": ("#b388ff", "rgba(179, 136, 255, 0.12)"),
    "Testing": ("#81ecec", "rgba(129, 236, 236, 0.12)"),
    "Build Tools": ("#ffeaa7", "rgba(255, 234, 167, 0.12)"),
    "Containers": ("#0984e3", "rgba(9, 132, 227, 0.12)"),
    "Terminal": ("#00e676", "rgba(0, 230, 118, 0.12)"),
}


class ToolRow(QFrame):
    """Single tool row — card style with checkbox, name, desc, version, category."""

    toggled = Signal(str, bool)

    def __init__(self, tool: dict, parent=None):
        super().__init__(parent)
        self.tool = tool
        self.key = tool.get("key", tool["name"])
        self._selected = False

        self.setStyleSheet(f"""
            ToolRow {{
                background-color: {BG_ROW};
                border: none;
                border-bottom: 1px solid {BORDER};
                margin: 0px;
            }}
        """)
        self.setFixedHeight(68)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(0)

        # Checkbox
        self.checkbox = QCheckBox()
        self.checkbox.setFixedWidth(36)
        self.checkbox.stateChanged.connect(self._on_check)
        layout.addWidget(self.checkbox)

        # Name + description column
        name_col = QVBoxLayout()
        name_col.setSpacing(3)
        name_col.setContentsMargins(0, 10, 0, 10)

        self.name_label = QLabel(tool.get("name", ""))
        self.name_label.setStyleSheet(f"""
            color: {FG};
            font-size: 14px;
            font-weight: 600;
            background: transparent;
        """)
        name_col.addWidget(self.name_label)

        desc_text = tool.get("description", "")
        if len(desc_text) > 80:
            desc_text = desc_text[:77] + "..."
        self.desc_label = QLabel(desc_text)
        self.desc_label.setStyleSheet(f"""
            color: {FG_MUTED};
            font-size: 11px;
            background: transparent;
        """)
        name_col.addWidget(self.desc_label)

        name_widget = QWidget()
        name_widget.setLayout(name_col)
        name_widget.setStyleSheet("background: transparent;")
        name_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        layout.addWidget(name_widget, stretch=1)

        # Version badge
        version = (
            tool.get("detect_cmd", "").split("--version")[0].strip()
            if "--version" in tool.get("detect_cmd", "")
            else ""
        )
        version_text = "—"
        if version:
            version_text = version.split()[-1] if version.split() else "—"

        self.version_label = QLabel(version_text)
        self.version_label.setFixedWidth(100)
        self.version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.version_label.setStyleSheet(f"""
            color: {FG_DIM};
            font-family: "JetBrains Mono", "Cascadia Code", "Consolas", monospace;
            font-size: 12px;
            background: transparent;
        """)
        layout.addWidget(self.version_label)

        layout.addSpacing(12)

        # Category badge with per-category color
        cat = tool.get("category", "Other")
        cat_fg, cat_bg = CATEGORY_COLORS.get(cat, (FG_DIM, BADGE_BG))
        cat_text = cat.upper()
        self.cat_badge = QLabel(cat_text)
        self.cat_badge.setFixedWidth(130)
        self.cat_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cat_badge.setStyleSheet(f"""
            QLabel {{
                background-color: {cat_bg};
                color: {cat_fg};
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 0.6px;
            }}
        """)
        layout.addWidget(self.cat_badge)

    def _on_check(self, state):
        self._selected = state == Qt.CheckState.Checked.value
        self._update_visual()
        self.toggled.emit(self.key, self._selected)

    def _update_visual(self):
        if self._selected:
            self.setStyleSheet(f"""
                ToolRow {{
                    background-color: {BG_ROW_SELECTED};
                    border: none;
                    border-bottom: 1px solid {BORDER_ACCENT};
                    border-left: 3px solid {ACCENT_PRIMARY};
                }}
            """)
        else:
            self.setStyleSheet(f"""
                ToolRow {{
                    background-color: {BG_ROW};
                    border: none;
                    border-bottom: 1px solid {BORDER};
                }}
            """)

    def is_checked(self) -> bool:
        return self.checkbox.isChecked()

    def set_checked(self, checked: bool):
        self.checkbox.setChecked(checked)

    def matches_filter(self, query: str, category: str) -> bool:
        if category != "All" and self.tool.get("category", "") != category:
            return False
        if query:
            name = self.tool.get("name", "").lower()
            desc = self.tool.get("description", "").lower()
            key = self.key.lower()
            if query not in name and query not in desc and query not in key:
                return False
        return True

    def enterEvent(self, event):
        if not self._selected:
            self.setStyleSheet(f"""
                ToolRow {{
                    background-color: {BG_ROW_HOVER};
                    border: none;
                    border-bottom: 1px solid {BORDER};
                }}
            """)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._update_visual()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self.checkbox.setChecked(not self.checkbox.isChecked())
        super().mousePressEvent(event)


class ColumnHeader(QWidget):
    """Column header row with select-all checkbox."""

    select_all_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(42)
        self.setStyleSheet(f"""
            background-color: {BG_CARD};
            border-bottom: 1px solid {BORDER};
            border-top-left-radius: 12px;
            border-top-right-radius: 12px;
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(0)

        self.select_all_cb = QCheckBox()
        self.select_all_cb.setFixedWidth(36)
        self.select_all_cb.stateChanged.connect(
            lambda state: self.select_all_changed.emit(
                state == Qt.CheckState.Checked.value
            )
        )
        layout.addWidget(self.select_all_cb)

        header_style = f"""
            color: {COLUMN_HEADER_FG};
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 1px;
            background: transparent;
        """

        name_header = QLabel("PACKAGE")
        name_header.setStyleSheet(header_style)
        layout.addWidget(name_header, stretch=1)

        version_header = QLabel("VERSION")
        version_header.setFixedWidth(100)
        version_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_header.setStyleSheet(header_style)
        layout.addWidget(version_header)

        layout.addSpacing(12)

        cat_header = QLabel("CATEGORY")
        cat_header.setFixedWidth(130)
        cat_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cat_header.setStyleSheet(header_style)
        layout.addWidget(cat_header)


class ToolTable(QWidget):
    """Scrollable list of tool rows with column headers."""

    selection_changed = Signal(int)

    def __init__(self, tools: list[dict], parent=None):
        super().__init__(parent)
        self._rows: list[ToolRow] = []

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(24, 8, 24, 0)
        outer_layout.setSpacing(0)

        self.column_header = ColumnHeader()
        self.column_header.select_all_changed.connect(self._on_select_all)
        outer_layout.addWidget(self.column_header)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {BG_CARD};
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
            }}
        """)

        self.list_widget = QWidget()
        self.list_widget.setStyleSheet(f"background-color: {BG_CARD};")
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(0)

        self._populate(tools)

        self.list_layout.addStretch()
        self.scroll_area.setWidget(self.list_widget)
        outer_layout.addWidget(self.scroll_area)

    def _populate(self, tools: list[dict]):
        for tool in tools:
            row = ToolRow(tool)
            row.toggled.connect(self._on_row_toggled)
            self._rows.append(row)
            self.list_layout.addWidget(row)

    def _on_row_toggled(self, key: str, checked: bool):
        count = sum(1 for r in self._rows if r.is_checked())
        self.selection_changed.emit(count)

    def _on_select_all(self, checked: bool):
        for row in self._rows:
            if row.isVisible():
                row.set_checked(checked)

    def apply_filter(self, query: str, category: str):
        for row in self._rows:
            visible = row.matches_filter(query, category)
            row.setVisible(visible)

    def selected_tools(self) -> list[dict]:
        return [r.tool for r in self._rows if r.is_checked()]

    def selected_count(self) -> int:
        return sum(1 for r in self._rows if r.is_checked())

    def clear_selection(self):
        self.column_header.select_all_cb.setChecked(False)
        for row in self._rows:
            row.set_checked(False)

    def select_tools_by_keys(self, keys: list[str]):
        """Select tools matching the given keys, uncheck everything else.

        Also resets the category filter to 'All' so matched tools are
        visible, and scrolls to the first matched row.
        """
        key_set = set(keys)
        first_matched_row = None

        for row in self._rows:
            should_check = row.key in key_set
            row.set_checked(should_check)
            row.setVisible(True)  # ensure visibility
            if should_check and first_matched_row is None:
                first_matched_row = row

        count = sum(1 for r in self._rows if r.is_checked())
        self.selection_changed.emit(count)

        # Scroll to first matched tool
        if first_matched_row is not None:
            from PySide6.QtCore import QTimer
            QTimer.singleShot(100, lambda: self.scroll_area.ensureWidgetVisible(
                first_matched_row, 0, 50
            ))

    def rebuild(self, tools: list[dict]):
        for row in self._rows:
            self.list_layout.removeWidget(row)
            row.deleteLater()
        self._rows.clear()

        # Remove the stretch item
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._populate(tools)
        self.list_layout.addStretch()
        self.selection_changed.emit(0)
