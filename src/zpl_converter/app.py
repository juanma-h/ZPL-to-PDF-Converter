from __future__ import annotations

import platform
import sys

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication

from .models import APP_DISPLAY_NAME, APP_NAME, APP_ORGANIZATION
from .ui.main_window import MainWindow


def configure_application_font(app: QApplication) -> None:
    family_candidates = {
        "Darwin": [".SF NS Text", "SF Pro Text", "Helvetica Neue", "Helvetica", "Arial"],
        "Windows": ["Segoe UI", "Arial", "Tahoma"],
    }.get(platform.system(), ["Noto Sans", "DejaVu Sans", "Arial"])

    available_families = set(QFontDatabase.families())
    for family in family_candidates:
        if family in available_families:
            app.setFont(QFont(family, 10))
            return


def main() -> None:
    app = QApplication(sys.argv)
    app.setOrganizationName(APP_ORGANIZATION)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_DISPLAY_NAME)
    configure_application_font(app)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
