# main.py
import sys
import os
import faulthandler
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QCoreApplication

# --- Add the project root to the Python path ---
# This is the crucial step that allows Python to find the 'src' package.
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Now we can import from the src package using absolute paths ---
# This must come AFTER the path is modified, as you correctly pointed out.
from src.ui.main_window import AICoderAssistant
from src.core.logging_config import setup_logging

# --- Ensure the config is loaded before any other operations ---


if __name__ == '__main__':
    # --- Setup logging as the very first application action ---
    setup_logging()
    
    # Enable the fault handler for better crash reports
    faulthandler.enable()
    
    app = QApplication(sys.argv)
    
    # Set application info for QSettings to work correctly
    QCoreApplication.setOrganizationName("AICoderOrg")
    QCoreApplication.setApplicationName("AICoderAssistant")

    # Create and show the main window
    window = AICoderAssistant()
    window.show()
    
    sys.exit(app.exec())