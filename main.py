# main.py
"""
AI Coder Assistant - Main Application Entry Point

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

Copyright (C) 2024 AI Coder Assistant Contributors
"""

import sys
import os
import faulthandler
import signal
import atexit
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QCoreApplication

# --- Add the project root to the Python path ---
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Import necessary components from the new frontend/backend structure ---
from src.frontend.ui.main_window import AICoderAssistant
from src.backend.services.logging_config import setup_logging

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print(f"\nReceived signal {signum}, shutting down gracefully...")
    if 'app' in globals() and app:
        app.quit()
    sys.exit(0)

def cleanup_on_exit():
    """Cleanup function called on exit."""
    print("Cleaning up on exit...")
    # The main window's closeEvent will handle thread cleanup

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
    # --- Set up signal handlers for graceful shutdown ---
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    atexit.register(cleanup_on_exit)
    
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