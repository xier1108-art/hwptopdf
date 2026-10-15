import sys

from PyQt6.QtWidgets import QApplication

from hwp2pdf.gui import MainWindow
from hwp2pdf.log import setup_logging


def main() -> None:
    setup_logging()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
