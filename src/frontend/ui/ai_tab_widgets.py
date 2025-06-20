"""
ai_tab_widgets.py

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

# src/frontend/ui/ai_tab_widgets.py
from typing import Any
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGroupBox,
                             QProgressBar, QFormLayout, QLineEdit, QComboBox, QTextEdit, QCheckBox)
from PyQt6.QtCore import Qt

def setup_ai_tab(parent_widget: QWidget, main_app_instance: Any) -> None:
    """
    Sets up the UI components for the AI code analysis tab.
    """
    layout = QVBoxLayout(parent_widget)

    # --- Model Selection Group ---
    model_group = QGroupBox("1. AI Model Configuration")
    model_layout = QFormLayout(model_group)

    main_app_instance.model_source_selector = QComboBox()
    main_app_instance.model_source_selector.addItem("Ollama")
    main_app_instance.model_source_selector.addItem("Own Trained Model")
    
    main_app_instance.ollama_model_label = QLabel("Ollama Model:")
    main_app_instance.ollama_model_selector = QComboBox()
    main_app_instance.refresh_button = QPushButton("Refresh Models")
    # Connect the refresh button to the populate_ollama_models method
    main_app_instance.refresh_button.clicked.connect(main_app_instance.populate_ollama_models)
    ollama_layout = QHBoxLayout()
    ollama_layout.addWidget(main_app_instance.ollama_model_selector)
    ollama_layout.addWidget(main_app_instance.refresh_button)
    # Expose the refresh button for main window connection
    if hasattr(parent_widget, 'refresh_button'):
        parent_widget.refresh_button = main_app_instance.refresh_button
    else:
        setattr(parent_widget, 'refresh_button', main_app_instance.refresh_button)

    main_app_instance.model_status_label = QLabel("Status: Not Loaded")
    main_app_instance.load_model_button = QPushButton("Load Trained Model")
    # Connect the load model button to the load_trained_model method (to be implemented)
    # main_app_instance.load_model_button.clicked.connect(main_app_instance.load_trained_model)

    model_layout.addRow(QLabel("Model Source:"), main_app_instance.model_source_selector)
    model_layout.addRow(main_app_instance.ollama_model_label, ollama_layout)
    model_layout.addRow(QLabel("Own Model Status:"), main_app_instance.model_status_label)
    model_layout.addRow(main_app_instance.load_model_button)
    
    layout.addWidget(model_group)

    # --- Scan Configuration Group ---
    scan_group = QGroupBox("2. Code Scanning")
    scan_layout = QFormLayout(scan_group)
    
    main_app_instance.scan_dir_entry = QLineEdit()
    main_app_instance.scan_dir_entry.setPlaceholderText("Select a project folder to scan...")
    main_app_instance.browse_button = QPushButton("Browse...")
    # Connect the browse button to the select_scan_directory method
    main_app_instance.browse_button.clicked.connect(main_app_instance.select_scan_directory)
    
    scan_dir_layout = QHBoxLayout()
    scan_dir_layout.addWidget(main_app_instance.scan_dir_entry)
    scan_dir_layout.addWidget(main_app_instance.browse_button)

    # Add include/exclude pattern fields
    main_app_instance.include_patterns_input = QLineEdit()
    main_app_instance.include_patterns_input.setPlaceholderText("*.py,*.js,*.java,*.cpp,*.c,*.h")
    main_app_instance.exclude_patterns_input = QLineEdit()
    main_app_instance.exclude_patterns_input.setPlaceholderText("(optional: e.g. tests/*,*.md)")
    scan_layout.addRow(QLabel("Include Patterns:"), main_app_instance.include_patterns_input)
    scan_layout.addRow(QLabel("Exclude Patterns:"), main_app_instance.exclude_patterns_input)

    # Add AI enhancement checkbox
    main_app_instance.ai_enhancement_checkbox = QCheckBox("Enable AI-Powered Analysis")
    main_app_instance.ai_enhancement_checkbox.setChecked(True)
    scan_layout.addRow(main_app_instance.ai_enhancement_checkbox)

    main_app_instance.scan_button = QPushButton("Start Scan")
    main_app_instance.scan_button.setFixedHeight(35)
    # Connect the scan button to the start_scan method
    main_app_instance.scan_button.clicked.connect(main_app_instance.start_scan)
    
    main_app_instance.stop_scan_button = QPushButton("Stop Scan")
    main_app_instance.stop_scan_button.setFixedHeight(35)
    main_app_instance.stop_scan_button.setEnabled(False)  # Initially disabled
    # Connect the stop scan button to the stop_scan method
    main_app_instance.stop_scan_button.clicked.connect(main_app_instance.stop_scan)
    
    scan_buttons_layout = QHBoxLayout()
    scan_buttons_layout.addWidget(main_app_instance.scan_button)
    scan_buttons_layout.addWidget(main_app_instance.stop_scan_button)
    
    main_app_instance.scan_progress_bar = QProgressBar()
    main_app_instance.scan_status_label = QLabel("Status: Idle")
    main_app_instance.scan_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    scan_layout.addRow(QLabel("Project Directory:"), scan_dir_layout)
    scan_layout.addRow(scan_buttons_layout)
    scan_layout.addRow(main_app_instance.scan_progress_bar)
    scan_layout.addRow(main_app_instance.scan_status_label)
    layout.addWidget(scan_group)

    # --- Results and Review Group ---
    results_group = QGroupBox("3. Results & Suggestions")
    results_layout = QVBoxLayout(results_group)

    main_app_instance.scan_results_text = QTextEdit()
    main_app_instance.scan_results_text.setReadOnly(True)
    main_app_instance.scan_results_text.setPlaceholderText("Scan report summary will appear here...")
    
    main_app_instance.review_suggestions_button = QPushButton("Review Suggestions Interactively")
    main_app_instance.review_suggestions_button.setEnabled(False)
    # Connect the review suggestions button to the review_next_suggestion method
    main_app_instance.review_suggestions_button.clicked.connect(main_app_instance.review_next_suggestion)
    
    main_app_instance.create_report_button = QPushButton("Generate Full Markdown Report")
    main_app_instance.create_report_button.setEnabled(False)
    # Connect the create report button to the start_report_generation method
    main_app_instance.create_report_button.clicked.connect(main_app_instance.start_report_generation)

    results_layout.addWidget(main_app_instance.scan_results_text)
    results_layout.addWidget(main_app_instance.review_suggestions_button)
    results_layout.addWidget(main_app_instance.create_report_button)
    layout.addWidget(results_group)

    layout.addStretch(1)
