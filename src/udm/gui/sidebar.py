"""Sidebar — category navigation with clean monochrome style."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from udm.gui.theme import (
    ACCENT_PRIMARY,
    BG_SIDEBAR,
    BORDER,
    FG_DIM,
    FG_MUTED,
)
from udm.gui.widgets import SidebarButton

# Category icon mapping — consistent Fluent emoji pack
CATEGORY_ICONS = {
    "All": "📦",
    "Languages": "💻",
    "Compilers": "⚙️",
    "SDKs": "🧩",
    "Frameworks": "🏗️",
    "Databases": "🗄️",
    "DevOps": "🔧",
    "DevOps Tools": "🔧",
    "Package Managers": "📋",
    "IDEs": "🖥️",
    "IDEs Editors": "🖥️",
    "Editors": "✏️",
    "Version Control": "🔀",
    "Cloud": "☁️",
    "Cloud CLIs": "☁️",
    "Mobile": "📱",
    "Mobile Development": "📱",
    "Web Dev": "🌐",
    "AI/ML": "🧠",
    "AI / Data Science": "🧠",
    "Testing": "🧪",
    "Security": "🔒",
    "Monitoring": "📊",
    "Containers": "🐳",
    "Build Tools": "🔨",
    "Terminal": "⌨️",
    "Virtualization": "🖥️",
    "SDKs Frameworks": "🧩",
    "Other": "📎",
}


class Sidebar(QWidget):
    """Sidebar with category navigation — monochrome dark dashboard style."""

    category_selected = Signal(str)

    def __init__(self, categories: list[str], tool_counts: dict[str, int], parent=None):
        super().__init__(parent)
        self.setFixedWidth(220)
        self.setStyleSheet(f"""
            background-color: {BG_SIDEBAR};
            border-right: 1px solid {BORDER};
        """)

        self._buttons: list[SidebarButton] = []
        self._active_category = "All"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 16, 0, 16)
        layout.setSpacing(0)

        # Section title
        section_title = QLabel("  CATEGORIES")
        section_title.setStyleSheet(f"""
            color: {FG_MUTED};
            font-size: 10px;
            font-weight: 600;
            letter-spacing: 1.5px;
            padding: 8px 20px;
            background: transparent;
        """)
        layout.addWidget(section_title)

        layout.addSpacing(4)

        # Scrollable category list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background: transparent;
            }}
        """)

        list_widget = QWidget()
        list_widget.setStyleSheet("background: transparent;")
        list_layout = QVBoxLayout(list_widget)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(2)

        # All category
        total = sum(tool_counts.values()) if tool_counts else 0
        all_btn = self._create_category_button("All", total)
        all_btn.set_active(True)
        list_layout.addWidget(all_btn)

        # Individual categories
        for cat in categories:
            count = tool_counts.get(cat, 0)
            btn = self._create_category_button(cat, count)
            list_layout.addWidget(btn)

        list_layout.addStretch()
        scroll.setWidget(list_widget)
        layout.addWidget(scroll)

        # Bottom stats
        layout.addSpacing(8)
        stats_label = QLabel(f"  {total} packages available")
        stats_label.setStyleSheet(f"""
            color: {FG_MUTED};
            font-size: 11px;
            padding: 8px 20px;
            background: transparent;
        """)
        layout.addWidget(stats_label)

    def _create_category_button(self, category: str, count: int) -> SidebarButton:
        icon = CATEGORY_ICONS.get(category, "·")
        btn = SidebarButton(f"{category}  ({count})", icon)
        btn.clicked.connect(lambda checked, c=category: self._on_category_clicked(c))
        self._buttons.append(btn)
        return btn

    def _on_category_clicked(self, category: str):
        self._active_category = category
        for btn in self._buttons:
            btn.set_active(False)
        # Find and activate the clicked button
        for btn in self._buttons:
            if category in btn.text():
                btn.set_active(True)
                break
        self.category_selected.emit(category)

    def set_categories(self, categories: list[str], tool_counts: dict[str, int]):
        """Rebuild sidebar categories (for refresh)."""
        # Clear old buttons
        for btn in self._buttons:
            btn.deleteLater()
        self._buttons.clear()
        # Note: full rebuild would require re-creating layout; for simplicity
        # we just update the active state
        self._active_category = "All"
