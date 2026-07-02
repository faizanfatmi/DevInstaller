"""Bottom action bar — Clear Selection + Install Selected buttons."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from udm.gui.theme import BG_WINDOW, FG_MUTED
from udm.gui.widgets import ActionButton


class ActionBar(QWidget):
    """Bottom buttons bar with clear and install actions."""

    clear_clicked = Signal()
    install_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {BG_WINDOW};")
        self.setFixedHeight(68)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 10, 24, 14)

        # Selection count label
        self.count_label = QLabel("No packages selected")
        self.count_label.setStyleSheet(f"""
            color: {FG_MUTED};
            font-size: 12px;
            font-weight: 400;
            background: transparent;
        """)
        layout.addWidget(self.count_label)

        layout.addStretch()

        self.clear_btn = ActionButton("Clear", "danger")
        self.clear_btn.clicked.connect(self.clear_clicked.emit)
        layout.addWidget(self.clear_btn)

        layout.addSpacing(10)

        self.install_btn = ActionButton("Install Selected", "primary")
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
