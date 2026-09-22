"""Collapsible system log panel — Terminal/Logs tabs matching mockup."""

from pathlib import Path
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPixmap, QTextCursor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from udm.gui.theme import (
    BG_CARD,
    BG_LOG,
    BORDER,
    FG,
    FG_DIM,
    FG_MUTED,
    GREEN,
    RED,
)

ICONS_DIR = Path(__file__).resolve().parent.parent / "assets" / "icons"


class _TabButton(QWidget):
    """A clickable tab widget with line icon, label, and underline indicator."""

    def __init__(self, icon_name: str, text: str, active: bool = False, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._active = active
        self._text = text
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(34)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(6)

        self.icon_lbl = QLabel()
        self.icon_lbl.setFixedSize(14, 14)
        self.icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_lbl.setStyleSheet("background: transparent; border: none;")
        icon_path = ICONS_DIR / icon_name
        if icon_path.exists():
            pix = QPixmap(str(icon_path))
            if not pix.isNull():
                self.icon_lbl.setPixmap(pix.scaled(14, 14, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        layout.addWidget(self.icon_lbl)

        self.text_lbl = QLabel(text)
        self.text_lbl.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(self.text_lbl)

        self._apply_style()

    def set_active(self, active: bool):
        self._active = active
        self._apply_style()

    def _apply_style(self):
        if self._active:
            self.setStyleSheet("""
                _TabButton {
                    border-bottom: 2px solid #6fdd78;
                    background: transparent;
                }
            """)
            self.text_lbl.setStyleSheet("color: #e1e2eb; font-size: 12px; font-weight: 600; background: transparent; border: none;")
        else:
            self.setStyleSheet("""
                _TabButton {
                    border-bottom: 2px solid transparent;
                    background: transparent;
                }
                _TabButton:hover {
                    background: rgba(255, 255, 255, 0.03);
                }
            """)
            self.text_lbl.setStyleSheet("color: #889484; font-size: 12px; font-weight: 500; background: transparent; border: none;")


class LogPanel(QWidget):
    """Terminal-style log output panel with Terminal/Logs tabs — DevForge Dark design."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._collapsed = False
        self._current_tab = "terminal"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 0)
        layout.setSpacing(0)

        # Header bar — tabs + actions
        header = QWidget()
        header.setStyleSheet("""
            QWidget {
                background-color: #0b0e14;
                border: 1px solid #3e4a3d;
                border-bottom: none;
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }
        """)
        header.setFixedHeight(34)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 0, 10, 0)
        header_layout.setSpacing(4)

        # Tab buttons with sidebar-style line icons
        self._terminal_tab = _TabButton("sb_languages.png", "Terminal", active=True)
        self._terminal_tab.mousePressEvent = lambda _: self._switch_tab("terminal")
        header_layout.addWidget(self._terminal_tab)

        self._logs_tab = _TabButton("meta_doc.png", "Logs", active=False)
        self._logs_tab.mousePressEvent = lambda _: self._switch_tab("logs")
        header_layout.addWidget(self._logs_tab)

        header_layout.addStretch()

        # Clear button with line trash icon
        clear_btn = QPushButton(" Clear")
        clear_btn.setFixedHeight(24)
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        trash_icon_path = ICONS_DIR / "icon_trash_silver.png"
        if trash_icon_path.exists():
            clear_btn.setIcon(QIcon(str(trash_icon_path)))
            clear_btn.setIconSize(QSize(13, 13))
        clear_btn.setStyleSheet("""
            QPushButton {
                background: #191c22;
                color: #becab9;
                border: 1px solid #3e4a3d;
                border-radius: 6px;
                font-size: 11px;
                font-weight: 500;
                padding: 2px 10px;
            }
            QPushButton:hover {
                color: #e1e2eb;
                background-color: #272a31;
                border-color: #6fdd78;
            }
        """)
        clear_btn.clicked.connect(self.clear_log)
        header_layout.addWidget(clear_btn)

        header_layout.addSpacing(6)

        # Expand toggle button with icon
        toggle_btn = QPushButton()
        toggle_btn.setFixedSize(24, 24)
        toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        expand_icon_path = ICONS_DIR / "icon_expand.png"
        if expand_icon_path.exists():
            toggle_btn.setIcon(QIcon(str(expand_icon_path)))
        toggle_btn.setStyleSheet("""
            QPushButton {
                background: #191c22;
                color: #becab9;
                border: 1px solid #3e4a3d;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #272a31;
            }
        """)
        toggle_btn.clicked.connect(self._toggle_collapse)
        self._toggle_btn = toggle_btn
        header_layout.addWidget(toggle_btn)

        layout.addWidget(header)

        # Log text area
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setFixedHeight(115)
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #0b0e14;
                border: 1px solid #3e4a3d;
                border-top: none;
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
                font-family: "Cascadia Code", "Consolas", monospace;
                font-size: 12px;
                line-height: 1.5;
                padding: 8px 14px;
                color: #becab9;
            }
        """)
        layout.addWidget(self.text_edit)
        self._text_widget = self.text_edit

        # Initialize with authentic prompt from mockup
        self.text_edit.append("<span style='color:#889484; font-weight:600;'>PS C:\\&gt; ▸</span>")
        self.text_edit.append("<span style='color:#a2c9ff;'>Checking for software updates...</span>")
        self.text_edit.append("<span style='color:#6fdd78;'>✓ DevInstaller is up to date.</span>")
        self.text_edit.append("<span style='color:#e1e2eb;'>Ready to install packages.</span>")

    def _switch_tab(self, tab: str):
        self._current_tab = tab
        self._terminal_tab.set_active(tab == "terminal")
        self._logs_tab.set_active(tab == "logs")

    def _toggle_collapse(self):
        self._collapsed = not self._collapsed
        self._text_widget.setVisible(not self._collapsed)

    def append_log(self, msg: str):
        color = FG_DIM
        ml = msg.lower()
        if "✓" in msg or "success" in ml or "installed" in ml:
            color = GREEN
        elif "✗" in msg or "fail" in ml or "error" in ml:
            color = RED
        elif "⚠" in msg or "warning" in ml or "skip" in ml:
            color = "#fbbf24"
        elif "checking" in ml or "download" in ml:
            color = "#a2c9ff"
        self.text_edit.append(f"<span style='color:{color};'>{msg}</span>")
        self.text_edit.moveCursor(QTextCursor.MoveOperation.End)

    def clear_log(self):
        self.text_edit.clear()
        self.text_edit.append("<span style='color:#889484; font-weight:600;'>PS C:\\&gt; ▸</span>")
