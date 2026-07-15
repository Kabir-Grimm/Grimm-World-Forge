import os
import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    icon_path = os.path.join(ROOT_DIR, "assets", "icon.ico")

    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = MainWindow()

    if os.path.exists(icon_path):
        window.setWindowIcon(QIcon(icon_path))

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()