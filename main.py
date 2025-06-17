# main.py
import sys
import os
import faulthandler
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QCoreApplication

# --- Add the project root to the Python path ---
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Import necessary components from the src package ---
from src.ui.main_window import AICoderAssistant
from src.core.logging_config import setup_logging

def create_project_directories():
    """
    Checks for and creates the necessary directories for the application to function.
    """
    print("Checking for necessary project directories...")
    # Get the project root from this script's location
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    # List of directories that the application needs
    required_dirs = [
        os.path.join(root_dir, "logs"),
        os.path.join(root_dir, "data"),
        os.path.join(root_dir, "data", "docs"),
        os.path.join(root_dir, "data", "learning_data"),
        os.path.join(root_dir, "data", "processed_data"),
        os.path.join(root_dir, "scripts"),
        os.path.join(root_dir, "tmp"),
        # Also create src subdirectories if they don't exist
        os.path.join(root_dir, "src", "logs"),
        os.path.join(root_dir, "src", "data"),
        os.path.join(root_dir, "src", "data", "docs"),
        os.path.join(root_dir, "src", "data", "learning_data"),
        os.path.join(root_dir, "src", "data", "processed_data")
    ]
    
    for dir_path in required_dirs:
        try:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                print(f"Created directory: {dir_path}")
        except OSError as e:
            print(f"Error creating directory {dir_path}: {e}")
            # Depending on the severity, you might want to exit or raise the exception
            # For this app, we'll just print the error and continue.
            
    print("Directory check complete.")


if __name__ == '__main__':
    # --- Create directories as the very first step ---
    create_project_directories()

    # Setup logging as the next application action
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