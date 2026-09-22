"""Sidebar — category navigation with DevForge Dark outline icons matching target design."""

from pathlib import Path
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from udm.gui.theme import (
    BG_SIDEBAR,
    BORDER,
    FG_DIM,
    FG_MUTED,
)

ICONS_DIR = Path(__file__).resolve().parent.parent / "assets" / "icons"

CATEGORY_CONFIG = [
    # (display_name, raw_category_key, icon_filename, default_count)
    ("AI / Data Science", "AI / Data Science", "sb_data_science.png", 6),
    ("Cloud CLIs", "Cloud CLIs", "sb_cloud.png", 3),
    ("Compilers", "Compilers", "sb_compilers.png", 22),
    ("Databases", "Databases", "sb_databases.png", 7),
    ("DevOps Tools", "DevOps & Tools", "sb_devops.png", 29),
    ("IDEs & Editors", "IDEs & Editors", "sb_ides.png", 5),
    ("Languages", "Languages", "sb_languages.png", 39),
    ("Mobile Dev", "Mobile Development", "sb_mobile.png", 3),
    ("Package Managers", "Package Managers", "sb_packages.png", 18),
    ("SDKs & Frameworks", "SDKs & Frameworks", "sb_sdks.png", 1),
]


class SidebarRow(QWidget):
    clicked = Signal(str)

    def __init__(self, category: str, display_name: str, icon_name: str, count: int, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.category = category
        self.display_name = display_name
        self.count = count
        self._active = False
        self.setFixedHeight(36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(10)

        self.icon_lbl = QLabel()
        self.icon_lbl.setFixedSize(20, 20)
        self.icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_lbl.setStyleSheet("background: transparent;")

        icon_path = ICONS_DIR / icon_name
        if icon_path.exists():
            pix = QPixmap(str(icon_path))
            if not pix.isNull():
                self.icon_lbl.setPixmap(pix.scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        layout.addWidget(self.icon_lbl)

        self.name_lbl = QLabel(display_name)
        layout.addWidget(self.name_lbl, stretch=1)

        count_str = f"{count:,}" if isinstance(count, int) else str(count)
        self.count_lbl = QLabel(count_str)
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
                    background-color: #1a1f26;
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    border-left: 3px solid #6fdd78;
                    border-radius: 6px;
                }
                QLabel {
                    border: none;
                }
            """)
            self.name_lbl.setStyleSheet("color: #ffffff; font-size: 13px; font-weight: 600; background: transparent; border: none;")
            self.count_lbl.setStyleSheet("""
                background-color: #22272e;
                color: #becab9;
                border: none;
                border-radius: 4px;
                padding: 2px 7px;
                font-size: 11px;
                font-weight: 600;
            """)
        else:
            self.setStyleSheet("""
                SidebarRow {
                    background-color: transparent;
                    border: 1px solid transparent;
                    border-radius: 6px;
                }
                SidebarRow:hover {
                    background-color: rgba(255, 255, 255, 0.04);
                }
                QLabel {
                    border: none;
                }
            """)
            self.name_lbl.setStyleSheet("color: #becab9; font-size: 13px; font-weight: 500; background: transparent; border: none;")
            self.count_lbl.setStyleSheet("""
                background-color: #20252c;
                color: #788574;
                border: none;
                border-radius: 4px;
                padding: 2px 7px;
                font-size: 11px;
                font-weight: 600;
            """)

    def mousePressEvent(self, event):
        self.clicked.emit(self.category)
        super().mousePressEvent(event)


class Sidebar(QWidget):
    """Sidebar with Toolchains header, modern outline icons, and DevForge Dark styling."""

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
        layout.setContentsMargins(10, 14, 10, 12)
        layout.setSpacing(0)

        # ── TOOLCHAINS header ──
        header_widget = QWidget()
        header_widget.setStyleSheet("background: transparent;")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(4, 4, 4, 8)
        header_layout.setSpacing(6)

        title_lbl = QLabel("TOOLCHAINS")
        title_lbl.setStyleSheet("""
            color: #738072;
            font-size: 10px;
            font-weight: 700;
            border: none;
            background: transparent;
        """)
        title_font = title_lbl.font()
        title_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.5)
        title_lbl.setFont(title_font)
        header_layout.addWidget(title_lbl)

        header_layout.addStretch()

        groups_badge = QLabel(f"{len(CATEGORY_CONFIG)} GROUPS")
        groups_badge.setStyleSheet("""
            color: #6fdd78;
            background-color: #141f17;
            border: 1px solid rgba(111, 221, 120, 0.28);
            border-radius: 4px;
            font-size: 9.5px;
            font-weight: 700;
            padding: 2px 6px;
        """)
        badge_font = groups_badge.font()
        badge_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.8)
        groups_badge.setFont(badge_font)
        header_layout.addWidget(groups_badge)

        layout.addWidget(header_widget)
        layout.addSpacing(6)

        # Scrollable category list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                background: transparent;
                width: 4px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #3e4a3d;
                min-height: 20px;
                border-radius: 2px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
        """)

        list_widget = QWidget()
        list_widget.setStyleSheet("background: transparent;")
        list_layout = QVBoxLayout(list_widget)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(4)

        # All Packages category (Storage/Archive box icon)
        total_count = sum(tool_counts.values()) if tool_counts else 129
        all_row = SidebarRow("All", "All Packages", "sb_all.png", total_count)
        all_row.clicked.connect(self._on_category_clicked)
        all_row.set_active(True)
        self._rows.append(all_row)
        list_layout.addWidget(all_row)

        # Categories matching mockup order and counts
        for display_name, raw_key, icon_name, default_count in CATEGORY_CONFIG:
            count = tool_counts.get(raw_key, default_count)
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
            background-color: #191c22;
            border: 1px solid #3e4a3d;
            border-radius: 6px;
        """)
        author_layout = QHBoxLayout(author_card)
        author_layout.setContentsMargins(8, 7, 8, 7)
        author_layout.setSpacing(6)

        author_lbl = QLabel("Author by <b>Faizan-Fatmi</b>")
        author_lbl.setStyleSheet("color: #becab9; font-size: 11px; background: transparent; border: none;")
        author_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        author_layout.addWidget(author_lbl)

        layout.addSpacing(6)
        layout.addWidget(author_card)

    def set_active_category(self, category: str):
        """Set active category row externally."""
        self._on_category_clicked(category)

    def _on_category_clicked(self, category: str):
        self._active_category = category
        for row in self._rows:
            row.set_active(row.category == category)
        self.category_selected.emit(category)
