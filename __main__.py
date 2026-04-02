# Steam Guide Downloader
# Copyright (c) 2025-2026 AlexAgents
# Licensed under the MIT License. See LICENSE file in the project root.

"""
Steam Guide Saver — entry point
"""
import sys
import os
import logging
from logging.handlers import RotatingFileHandler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.paths import get_log_path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        RotatingFileHandler(
            get_log_path(), encoding="utf-8",
            maxBytes=5 * 1024 * 1024, backupCount=3
        ),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def main():
    try:
        from PyQt6.QtWidgets import QApplication
        from app.gui.main_window import MainWindow
        from app.gui.icon_provider import setup_app_icon
        from app import APP_NAME, APP_VERSION

        logger.info(f"Starting {APP_NAME} v{APP_VERSION}")

        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        app.setApplicationName(APP_NAME)
        app.setApplicationVersion(APP_VERSION)

        window = MainWindow()
        setup_app_icon(app, window)
        window.show()

        sys.exit(app.exec())

    except ImportError as e:
        logger.critical(f"Missing dependency: {e}")
        print(f"\n{e}")
        print("pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()