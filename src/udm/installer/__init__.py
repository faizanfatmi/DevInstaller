"""Installation engine package."""

from udm.installer.batch import install_selected
from udm.installer.callbacks import set_log_callback, set_progress_callback
from udm.installer.engine import (
    can_uninstall,
    detect_tool,
    install_tool,
    setup_path,
    uninstall_tool,
)
from udm.installer.oracle import is_oracle_tool, oracle_lifecycle

__all__ = [
    "set_progress_callback",
    "set_log_callback",
    "detect_tool",
    "install_tool",
    "uninstall_tool",
    "can_uninstall",
    "setup_path",
    "install_selected",
    "is_oracle_tool",
    "oracle_lifecycle",
]

