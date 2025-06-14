# main.py
import faulthandler
import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QCoreApplication

# Enable the fault handler to get a traceback on segfaults
faulthandler.enable()

# Set application info for QSettings to work correctly across the app
QCoreApplication.setOrganizationName("AICoderOrg")
QCoreApplication.setApplicationName("AICoderAssistant")

# Import the main window class
from main_window import AICoderAssistant

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AICoderAssistant()
    window.show()
    sys.exit(app.exec())