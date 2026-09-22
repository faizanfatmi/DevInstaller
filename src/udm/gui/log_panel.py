"""Collapsible system log panel — Terminal/Logs tabs matching mockup."""

from pathlib import Path
from PySide6.QtCore import Qt
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


class _TabButton(QLabel):
    """A clickable tab label with underline indicator."""

    def __init__(self, icon: str, text: str, active: bool = False, parent=None):
        super().__init__(f"{icon}  {text}", parent)
        self._active = active
        self._text = text
        self._icon = icon
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._apply_style()

    def set_active(self, active: bool):
        self._active = active
        self._apply_style()

    def _apply_style(self):
        if self._active:
            self.setStyleSheet("""
                QLabel {
                    color: #ffffff;
                    font-size: 12.5px;
                    font-weight: 600;
                    padding: 8px 16px;
                    border-bottom: 2px solid #6366f1;
                    background: transparent;
                }
            """)
        else:
            self.setStyleSheet("""
                QLabel {
                    color: #64748b;
                    font-size: 12.5px;
                    font-weight: 500;
                    padding: 8px 16px;
                    border-bottom: 2px solid transparent;
                    background: transparent;
                }
                QLabel:hover {
                    color: #94a3b8;
                }
            """)


class LogPanel(QWidget):
    """Terminal-style log output panel with Terminal/Logs tabs — matching mockup."""

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
                background-color: rgba(15, 23, 42, 0.9);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-bottom: none;
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }
        """)
        header.setFixedHeight(34)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 0, 10, 0)
        header_layout.setSpacing(4)

        # Tab buttons
        self._terminal_tab = _TabButton(">_", "Terminal", active=True)
        self._terminal_tab.mousePressEvent = lambda _: self._switch_tab("terminal")
        header_layout.addWidget(self._terminal_tab)

        self._logs_tab = _TabButton("📄", "Logs", active=False)
        self._logs_tab.mousePressEvent = lambda _: self._switch_tab("logs")
        header_layout.addWidget(self._logs_tab)

        header_layout.addStretch()

        # Clear button
        clear_btn = QPushButton("🗑  Clear")
        clear_btn.setFixedHeight(24)
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.03);
                color: #94a3b8;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 6px;
                font-size: 11px;
                font-weight: 500;
                padding: 2px 10px;
            }
            QPushButton:hover {
                color: #ffffff;
                background-color: rgba(255, 255, 255, 0.08);
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
                background: rgba(255, 255, 255, 0.03);
                color: #94a3b8;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.08);
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
                background-color: rgba(10, 15, 28, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-top: none;
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
                font-family: "Cascadia Code", "Consolas", monospace;
                font-size: 12px;
                line-height: 1.5;
                padding: 8px 14px;
                color: #94a3b8;
            }
        """)
        layout.addWidget(self.text_edit)
        self._text_widget = self.text_edit

        # Initialize with authentic prompt from mockup
        self.text_edit.append("<span style='color:#94a3b8; font-weight:600;'>PS C:\\&gt; ▸</span>")
        self.text_edit.append("<span style='color:#38bdf8;'>🔍 Checking for software updates...</span>")
        self.text_edit.append("<span style='color:#4ade80;'>✓ DevInstaller is up to date.</span>")
        self.text_edit.append("<span style='color:#f1f5f9;'>Ready to install packages! 🚀</span>")

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
            color = "#38bdf8"
        self.text_edit.append(f"<span style='color:{color};'>{msg}</span>")
        self.text_edit.moveCursor(QTextCursor.MoveOperation.End)

    def clear_log(self):
        self.text_edit.clear()
        self.text_edit.append("<span style='color:#94a3b8; font-weight:600;'>PS C:\\&gt; ▸</span>")
