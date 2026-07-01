"""Application entry point."""

import sys

from udm.logger import logger
from udm.platform import is_admin, is_windows, request_admin


def main():
    logger.info("═══ DevInstaller started ═══")

    if is_windows() and not is_admin():
        if "--elevate" in sys.argv:
            logger.info("Requesting UAC elevation…")
            try:
                request_admin()
            except Exception:
                logger.warning("UAC elevation failed — continuing without admin.")
        else:
            logger.warning(
                "Running without admin privileges. "
                "Some installations may need admin. "
                "Relaunch with --elevate for full access."
            )

    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication

    from udm.config import resource_path
    from udm.constants import LOGO_FILENAME
    from udm.gui import MainWindow

    app = QApplication(sys.argv)

    logo = resource_path(LOGO_FILENAME)
    if logo.exists():
        app.setWindowIcon(QIcon(str(logo)))
    else:
        logger.warning(f"Logo not found at {logo}; using default icon.")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
