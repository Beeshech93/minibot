"""
POCKET MINI BOT PRO — Main Desktop Application Entry Point
Private Visual Trading Analysis Assistant for macOS (Pocket Option).
"""
import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# Ensure package root is in sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Pocket Mini Bot Pro")
    app.setOrganizationName("PocketMiniBot")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

