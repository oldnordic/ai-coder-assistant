import faulthandler
import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QCoreApplication

# NEW: Enable the fault handler to get a traceback on segfaults
faulthandler.enable()

# Set application info for QSettings to work correctly across the app
QCoreApplication.setOrganizationName("AICoderOrg")
QCoreApplication.setApplicationName("AICoderAssistant")

# Direct import for a flat structure
from main_window import AIFoundryApp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AIFoundryApp()
    window.show()
    sys.exit(app.exec_())