"""Bottom action bar — slim separator with selection count.

The primary install button has been moved to the detail panel. This bar now
serves as a thin status row showing the current selection count.
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from udm.gui.theme import BG_WINDOW, BORDER, FG_MUTED
from udm.gui.widgets import ActionButton


class ActionBar(QWidget):
    """Slim bottom bar showing selection count and quick actions."""

    clear_clicked = Signal()
    install_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            background-color: {BG_WINDOW};
            border-top: 1px solid {BORDER};
        """)
        self.setFixedHeight(44)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 6, 24, 6)

        # Selection count label
        self.count_label = QLabel("No packages selected")
        self.count_label.setStyleSheet(f"""
            color: #becab9;
            font-size: 11px;
            font-weight: 400;
            background: transparent;
        """)
        layout.addWidget(self.count_label)

        layout.addStretch()

        # Clear button (small, secondary)
        self.clear_btn = ActionButton("Clear", "secondary")
        self.clear_btn.setFixedHeight(28)
        self.clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: #889484;
                border: 1px solid #3e4a3d;
                border-radius: 6px;
                padding: 4px 16px;
                font-size: 11px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                color: #e1e2eb;
                background-color: #191c22;
                border-color: #889484;
            }}
        """)
        self.clear_btn.clicked.connect(self.clear_clicked.emit)
        layout.addWidget(self.clear_btn)

        layout.addSpacing(8)

        # Install button (compact)
        self.install_btn = ActionButton("Install Selected", "primary")
        self.install_btn.setFixedHeight(28)
        self.install_btn.setEnabled(False)
        self.install_btn.clicked.connect(self.install_clicked.emit)
        layout.addWidget(self.install_btn)

    def update_state(self, selected_count: int):
        self.install_btn.setEnabled(selected_count > 0)
        if selected_count > 0:
            self.install_btn.setText(f"Install ({selected_count})")
            self.count_label.setText(f"{selected_count} package{'s' if selected_count != 1 else ''} selected")
        else:
            self.install_btn.setText("Install Selected")
            self.count_label.setText("No packages selected")
