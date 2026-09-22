"""Scrollable tool list with deep navy card-style rows matching target mockup."""

from pathlib import Path
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox, QFrame, QHBoxLayout, QLabel,
    QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)
from PySide6.QtGui import QPixmap

from udm.gui.theme import (
    BORDER, FG, FG_DIM, FG_MUTED,
)

ICONS_DIR = Path(__file__).resolve().parent.parent / "assets" / "icons"

# Category color mapping — DevForge Dark palette
CATEGORY_COLORS = {
    "Languages": ("#a2c9ff", "rgba(162, 201, 255, 0.15)"),
    "Package Managers": ("#becab9", "rgba(190, 202, 185, 0.15)"),
    "Compilers": ("#6fdd78", "rgba(111, 221, 120, 0.15)"),
    "Databases": ("#a2c9ff", "rgba(162, 201, 255, 0.15)"),
    "DevOps Tools": ("#becab9", "rgba(190, 202, 185, 0.15)"),
    "DevOps & Tools": ("#becab9", "rgba(190, 202, 185, 0.15)"),
    "IDEs & Editors": ("#6fdd78", "rgba(111, 221, 120, 0.15)"),
    "Cloud CLIs": ("#a2c9ff", "rgba(162, 201, 255, 0.15)"),
    "Mobile Development": ("#d5bbff", "rgba(213, 187, 255, 0.15)"),
    "Data Science": ("#d5bbff", "rgba(213, 187, 255, 0.15)"),
    "AI / Data Science": ("#d5bbff", "rgba(213, 187, 255, 0.15)"),
    "SDKs & Frameworks": ("#d5bbff", "rgba(213, 187, 255, 0.15)"),
}

TOOL_ICONS_MAP = {
    "python": "python.png",
    "python311": "python.png",
    "pip": "pip.png",
    "gcc": "gcc.png",
    "gpp": "cpp.png",
}


class ElidedLabel(QLabel):
    """QLabel that automatically truncates text with an ellipsis (...) to fit its width."""

    def __init__(self, text: str = "", parent=None):
        super().__init__(parent)
        self._full_text = text
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        if text:
            self._update_elide()

    def setText(self, text: str):
        self._full_text = text
        self._update_elide()

    def set_full_text(self, text: str):
        self._full_text = text
        self._update_elide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_elide()

    def _update_elide(self):
        if not self._full_text:
            super().setText("")
            return
        w = self.width()
        if w <= 10:
            super().setText("")
            return
        fm = self.fontMetrics()
        elided = fm.elidedText(self._full_text, Qt.TextElideMode.ElideRight, w)
        super().setText(elided)


class ToolRow(QFrame):
    toggled = Signal(str, bool)
    clicked = Signal(dict)

    def __init__(self, tool, parent=None):
        super().__init__(parent)
        self.tool = tool
        self.key = tool.get("key", tool["name"])
        self._selected = False

        self.setObjectName("toolRow")
        self.setFixedHeight(58)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_style()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(6)

        # Checkbox
        self.checkbox = QCheckBox()
        self.checkbox.setFixedWidth(20)
        self.checkbox.setStyleSheet("""
            QCheckBox {
                background: transparent;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1.5px solid #484F58;
                border-radius: 4px;
                background-color: transparent;
            }
            QCheckBox::indicator:hover {
                border: 1.5px solid #6fdd78;
            }
            QCheckBox::indicator:checked {
                background-color: #6fdd78;
                border: 1.5px solid #6fdd78;
                image: url("e:/faizan/Faizan/Github/DevInstaller/src/udm/assets/icons/check.png");
            }
        """)
        self.checkbox.stateChanged.connect(self._on_check)
        layout.addWidget(self.checkbox)

        # Tool icon
        from udm.gui.icon_provider import get_tool_icon_pixmap
        icon_label = QLabel()
        icon_label.setFixedSize(26, 26)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("background: transparent; border: none;")

        pix = get_tool_icon_pixmap(tool, size=24)
        if pix and not pix.isNull():
            icon_label.setPixmap(pix)
        layout.addWidget(icon_label)

        # Name and description column (auto-elided so it never overflows or overlaps)
        name_col = QVBoxLayout()
        name_col.setSpacing(1)
        name_col.setContentsMargins(0, 6, 0, 6)

        display_title = "C++" if self.key == "gpp" else tool.get("name", "")
        self.name_label = ElidedLabel(display_title)
        self.name_label.setStyleSheet("color: #e1e2eb; font-size: 13.5px; font-weight: 600; background: transparent; border: none;")
        name_col.addWidget(self.name_label)

        desc_text = tool.get("description", "")
        self.desc_label = ElidedLabel(desc_text)
        self.desc_label.setStyleSheet("color: #becab9; font-size: 11px; background: transparent; border: none;")
        name_col.addWidget(self.desc_label)

        name_widget = QWidget()
        name_widget.setMinimumWidth(0)
        name_widget.setLayout(name_col)
        name_widget.setStyleSheet("background: transparent; border: none;")
        name_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(name_widget, stretch=1)

        # Version column
        version = (tool.get("detect_cmd", "").split("--version")[0].strip()
            if "--version" in tool.get("detect_cmd", "") else "")
        version_text = "—"
        if version:
            version_text = version.split()[-1] if version.split() else "—"
        self.version_label = QLabel(version_text)
        self.version_label.setFixedWidth(72)
        self.version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.version_label.setStyleSheet("""
            color: #889484;
            font-family: "Cascadia Code", "Consolas", monospace;
            font-size: 10px;
            background: transparent;
            border: none;
        """)
        layout.addWidget(self.version_label)

        # Category badge (compact labels to guarantee zero clipping)
        cat = tool.get("category", "Other")
        if cat in ("DevOps & Tools", "DevOps Tools"):
            cat_display = "DEVOPS"
        elif cat in ("AI / Data Science", "Data Science"):
            cat_display = "DATA SCIENCE"
        elif cat == "Package Managers":
            cat_display = "PKG MANAGERS"
        elif cat == "Mobile Development":
            cat_display = "MOBILE DEV"
        elif cat == "SDKs & Frameworks":
            cat_display = "SDKS"
        elif cat == "IDEs & Editors":
            cat_display = "IDES & EDITORS"
        else:
            cat_display = cat.upper()

        cat_fg, cat_bg = CATEGORY_COLORS.get(cat, ("#becab9", "rgba(255, 255, 255, 0.08)"))
        self.cat_badge = QLabel(cat_display)
        self.cat_badge.setFixedWidth(98)
        self.cat_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cat_badge.setStyleSheet(f"""
            color: {cat_fg};
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 0.4px;
            background: transparent;
            border: none;
        """)
        layout.addWidget(self.cat_badge)

        # Status badge (ALWAYS visible with fixed width so columns never shift)
        self._is_installed = False
        self.status_badge = QLabel("")
        self.status_badge.setFixedWidth(66)
        self.status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_badge.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(self.status_badge)

    def _apply_style(self):
        if self._selected:
            self.setStyleSheet("""
                QFrame#toolRow {
                    background-color: #1d2026;
                    border: 1px solid #6fdd78;
                    border-radius: 10px;
                }
                QLabel { border: none; background: transparent; }
                QWidget { border: none; background: transparent; }
            """)
        else:
            self.setStyleSheet("""
                QFrame#toolRow {
                    background-color: #191c22;
                    border: 1px solid #3e4a3d;
                    border-radius: 10px;
                }
                QFrame#toolRow:hover {
                    background-color: #272a31;
                    border: 1px solid rgba(111, 221, 120, 0.35);
                }
                QLabel { border: none; background: transparent; }
                QWidget { border: none; background: transparent; }
            """)

    def _on_check(self, state):
        self._selected = state == Qt.CheckState.Checked.value
        self._apply_style()
        self.toggled.emit(self.key, self._selected)

    def is_checked(self): return self.checkbox.isChecked()
    def set_checked(self, checked): self.checkbox.setChecked(checked)

    def set_installed(self, installed: bool):
        self._is_installed = bool(installed)
        if self._is_installed:
            self.status_badge.setText("INSTALLED")
            self.status_badge.setStyleSheet("""
                color: #6fdd78;
                font-size: 9px;
                font-weight: 700;
                background-color: rgba(111, 221, 120, 0.15);
                border: 1px solid rgba(111, 221, 120, 0.35);
                border-radius: 5px;
                padding: 2px 2px;
            """)
        else:
            self.status_badge.setText("")
            self.status_badge.setStyleSheet("background: transparent; border: none;")

    def matches_filter(self, query, category):
        if category != "All" and self.tool.get("category", "") != category:
            # Handle mapped categories
            if category == "AI / Data Science" and self.tool.get("category", "") == "Data Science":
                pass
            elif category == "DevOps & Tools" and self.tool.get("category", "") == "DevOps Tools":
                pass
            else:
                return False
        if query:
            name = self.tool.get("name", "").lower()
            desc = self.tool.get("description", "").lower()
            key = self.key.lower()
            if query in name or query in desc or query in key:
                return True
            # Multi-word match: each word in query appears in tool's text
            terms = query.split()
            combined = f"{key} {name} {desc}"
            if terms and all(t in combined for t in terms):
                return True
            # Normalized match (ignoring spaces / hyphens)
            norm_q = query.replace(" ", "").replace("-", "")
            if norm_q and (norm_q in combined.replace(" ", "").replace("-", "")):
                return True
            # Check TECH_ALIASES
            from udm.stack_parser import TECH_ALIASES
            if TECH_ALIASES.get(query) == key or TECH_ALIASES.get(norm_q) == key:
                return True
            return False
        return True

    def mousePressEvent(self, event):
        self.checkbox.setChecked(not self.checkbox.isChecked())
        self.clicked.emit(self.tool)
        super().mousePressEvent(event)


class ColumnHeader(QWidget):
    select_all_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(28)
        self.setStyleSheet("background: transparent; border: none;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 16, 0)
        layout.setSpacing(6)

        self.select_all_cb = QCheckBox()
        self.select_all_cb.setFixedWidth(20)
        self.select_all_cb.setStyleSheet("""
            QCheckBox { background: transparent; }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1.5px solid #484F58;
                border-radius: 4px;
                background-color: transparent;
            }
            QCheckBox::indicator:hover {
                border: 1.5px solid #6fdd78;
            }
            QCheckBox::indicator:checked {
                background-color: #6fdd78;
                border: 1.5px solid #6fdd78;
                image: url("e:/faizan/Faizan/Github/DevInstaller/src/udm/assets/icons/check.png");
            }
        """)
        self.select_all_cb.stateChanged.connect(
            lambda s: self.select_all_changed.emit(s == Qt.CheckState.Checked.value)
        )
        layout.addWidget(self.select_all_cb)

        # Icon spacer placeholder (matching 26px icon in ToolRow)
        icon_spacer = QWidget()
        icon_spacer.setFixedWidth(26)
        icon_spacer.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(icon_spacer)

        hs = "color: #889484; font-size: 11px; font-weight: 700; letter-spacing: 0.8px; background: transparent; border: none;"

        name_header = QLabel("PACKAGE")
        name_header.setStyleSheet(hs)
        layout.addWidget(name_header, stretch=1)

        version_header = QLabel("VERSION")
        version_header.setFixedWidth(72)
        version_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_header.setStyleSheet(hs)
        layout.addWidget(version_header)

        cat_header = QLabel("CATEGORY")
        cat_header.setFixedWidth(98)
        cat_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cat_header.setStyleSheet(hs)
        layout.addWidget(cat_header)

        status_header = QLabel("STATUS")
        status_header.setFixedWidth(66)
        status_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_header.setStyleSheet(hs)
        layout.addWidget(status_header)


class ToolTable(QWidget):
    selection_changed = Signal(int)
    tool_selected = Signal(dict)

    def __init__(self, tools, parent=None):
        super().__init__(parent)
        self._rows = []
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(12, 2, 12, 0)
        outer_layout.setSpacing(4)

        self.column_header = ColumnHeader()
        self.column_header.select_all_changed.connect(self._on_select_all)
        outer_layout.addWidget(self.column_header)

        self.scroll_area = QScrollArea()
        self.scroll_area.setMinimumHeight(180)
        self.scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                width: 6px;
                background: transparent;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #3e4a3d;
                border-radius: 3px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #889484;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        self.list_widget = QWidget()
        self.list_widget.setStyleSheet("background: transparent;")
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(6)

        self._populate(tools)
        self.list_layout.addStretch()
        self.scroll_area.setWidget(self.list_widget)
        outer_layout.addWidget(self.scroll_area)

    def _populate(self, tools):
        for tool in tools:
            row = ToolRow(tool)
            row.toggled.connect(self._on_row_toggled)
            row.clicked.connect(self._on_row_clicked)
            self._rows.append(row)
            self.list_layout.addWidget(row)

    def _on_row_toggled(self, key, checked):
        self.selection_changed.emit(sum(1 for r in self._rows if r.is_checked()))

    def _on_row_clicked(self, tool):
        self.tool_selected.emit(tool)

    def _on_select_all(self, checked):
        for row in self._rows:
            if row.isVisible(): row.set_checked(checked)

    def apply_filter(self, query, category):
        for row in self._rows: row.setVisible(row.matches_filter(query, category))

    def selected_tools(self): return [r.tool for r in self._rows if r.is_checked()]
    get_selected_tools = selected_tools
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

    def update_tool_installed(self, key: str, is_installed: bool):
        for row in self._rows:
            if row.key == key:
                row.set_installed(is_installed)
                break
