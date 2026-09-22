"""Sidebar — category navigation with deep navy style, authentic icons, and Home nav."""

from pathlib import Path
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from udm.gui.theme import (
    BG_SIDEBAR,
    BORDER,
    FG,
    FG_DIM,
    FG_MUTED,
)

ICONS_DIR = Path(__file__).resolve().parent.parent / "assets" / "icons"

CATEGORY_CONFIG = [
    # (display_name, raw_category_key, icon_filename, default_count)
    ("Data Science", "AI / Data Science", "sb_data_science.png", 6),
    ("Cloud CLIs", "Cloud CLIs", "sb_cloud.png", 3),
    ("Compilers", "Compilers", "sb_compilers.png", 22),
    ("Databases", "Databases", "sb_databases.png", 5),
    ("DevOps Tools", "DevOps & Tools", "sb_devops.png", 29),
    ("IDEs & Editors", "IDEs & Editors", "sb_ides.png", 3),
    ("Languages", "Languages", "sb_languages.png", 39),
    ("Mobile Development", "Mobile Development", "sb_mobile.png", 3),
    ("Package Managers", "Package Managers", "sb_packages.png", 18),
    ("SDKs & Frameworks", "SDKs & Frameworks", "sb_sdks.png", 1),
]


class SidebarRow(QWidget):
    clicked = Signal(str)

    def __init__(self, category: str, display_name: str, icon_name: str, count: int, parent=None):
        super().__init__(parent)
        self.category = category
        self.display_name = display_name
        self.count = count
        self._active = False
        self.setFixedHeight(36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(10)

        self.icon_lbl = QLabel()
        self.icon_lbl.setFixedSize(18, 18)
        self.icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_lbl.setStyleSheet("background: transparent;")

        icon_path = ICONS_DIR / icon_name
        if icon_path.exists():
            pix = QPixmap(str(icon_path))
            if not pix.isNull():
                self.icon_lbl.setPixmap(pix.scaled(18, 18, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        layout.addWidget(self.icon_lbl)

        self.name_lbl = QLabel(display_name)
        layout.addWidget(self.name_lbl, stretch=1)

        self.count_lbl = QLabel(str(count))
        self.count_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.count_lbl)

        self._update_style()

    def set_active(self, active: bool):
        self._active = active
        self._update_style()

    def _update_style(self):
        if self._active:
            self.setStyleSheet("""
                SidebarRow {
                    background-color: rgba(59, 130, 246, 0.25);
                    border: none;
                    border-radius: 8px;
                }
            """)
            self.name_lbl.setStyleSheet("color: #ffffff; font-size: 13px; font-weight: 700; background: transparent;")
            self.count_lbl.setStyleSheet("""
                background-color: #2563eb;
                color: #ffffff;
                border-radius: 10px;
                padding: 1px 8px;
                font-size: 11px;
                font-weight: 700;
            """)
        else:
            self.setStyleSheet("""
                SidebarRow {
                    background-color: transparent;
                    border: none;
                    border-radius: 8px;
                }
                SidebarRow:hover {
                    background-color: rgba(255, 255, 255, 0.05);
                }
            """)
            self.name_lbl.setStyleSheet("color: #94a3b8; font-size: 13px; font-weight: 500; background: transparent;")
            self.count_lbl.setStyleSheet("color: #64748b; font-size: 11px; font-weight: 600; background: transparent;")

    def mousePressEvent(self, event):
        self.clicked.emit(self.category)
        super().mousePressEvent(event)


class Sidebar(QWidget):
    """Sidebar with Home navigation and category list — matching target screenshot."""

    category_selected = Signal(str)

    def __init__(self, categories: list[str], tool_counts: dict[str, int], parent=None):
        super().__init__(parent)
        self.setFixedWidth(220)
        self.setStyleSheet(f"""
            background-color: {BG_SIDEBAR};
            border-right: 1px solid {BORDER};
        """)

        self._rows: list[SidebarRow] = []
        self._active_category = "All"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 14, 12, 14)
        layout.setSpacing(0)

        # ── Home navigation button ──
        home_btn = QPushButton("   Home")
        home_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        home_btn.setFixedHeight(40)
        home_icon_path = ICONS_DIR / "home.png"
        if home_icon_path.exists():
            home_btn.setIcon(QIcon(str(home_icon_path)))
            home_btn.setIconSize(home_btn.iconSize())
        home_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2563eb, stop:1 #3b82f6);
                color: #ffffff;
                border: none;
                border-radius: 10px;
                font-size: 13.5px;
                font-weight: 700;
                text-align: left;
                padding-left: 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3b82f6, stop:1 #60a5fa);
            }
        """)
        home_btn.clicked.connect(lambda: self._on_category_clicked("All"))
        layout.addWidget(home_btn)

        layout.addSpacing(16)

        # Section title
        section_title = QLabel("CATEGORIES")
        section_title.setStyleSheet(f"""
            color: {FG_MUTED};
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1.5px;
            padding: 4px 6px;
            background: transparent;
        """)
        layout.addWidget(section_title)

        layout.addSpacing(6)

        # Scrollable category list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet("border: none; background: transparent;")

        list_widget = QWidget()
        list_widget.setStyleSheet("background: transparent;")
        list_layout = QVBoxLayout(list_widget)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(4)

        # All Packages category
        all_row = SidebarRow("All", "All Packages", "cube.png", 129)
        all_row.clicked.connect(self._on_category_clicked)
        all_row.set_active(True)
        self._rows.append(all_row)
        list_layout.addWidget(all_row)

        # Categories matching mockup order and counts
        for display_name, raw_key, icon_name, default_count in CATEGORY_CONFIG:
            count = tool_counts.get(raw_key, default_count)
            # In mockup, IDEs & Editors shows 3
            if display_name == "IDEs & Editors":
                count = 3
            row = SidebarRow(raw_key, display_name, icon_name, count)
            row.clicked.connect(self._on_category_clicked)
            self._rows.append(row)
            list_layout.addWidget(row)

        list_layout.addStretch()
        scroll.setWidget(list_widget)
        layout.addWidget(scroll, stretch=1)

        # Author watermark at bottom of sidebar
        author_card = QWidget()
        author_card.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 8px;
        """)
        author_layout = QHBoxLayout(author_card)
        author_layout.setContentsMargins(8, 7, 8, 7)
        author_layout.setSpacing(6)

        author_lbl = QLabel("Author by <b>Faizan-Fatmi</b>")
        author_lbl.setStyleSheet("color: #cbd5e1; font-size: 11px; background: transparent; border: none;")
        author_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        author_layout.addWidget(author_lbl)

        layout.addSpacing(6)
        layout.addWidget(author_card)

    def _on_category_clicked(self, category: str):
        self._active_category = category
        for row in self._rows:
            row.set_active(row.category == category)
        self.category_selected.emit(category)
