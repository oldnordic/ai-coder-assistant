import sys
import os
from PyQt5.QtWidgets import QApplication

# --- Corrected Path Setup ---
# This ensures Python knows where to find the 'ai_coder_assistant' package
# by adding the parent directory to the system path.
current_file_path = os.path.abspath(__file__)
package_dir = os.path.dirname(current_file_path)
project_root = os.path.dirname(package_dir)

if project_root not in sys.path:
    sys.path.insert(0, project_root)


# --- Corrected Import Statement ---
# This now correctly imports AIFoundryApp from within the package structure.
from ai_coder_assistant.main_window import AIFoundryApp


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AIFoundryApp()
    window.show()
    sys.exit(app.exec_())