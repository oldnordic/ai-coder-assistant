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

import os

# src/frontend/ui/ai_tab_widgets.py
from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


def setup_ai_tab(parent_widget: QWidget, main_app_instance: Any) -> None:
    """
    Sets up the UI components for the AI code analysis tab.
    """
    # Initialize widget dictionary for AI tab
    if not hasattr(main_app_instance, "widgets"):
        main_app_instance.widgets = {}
    main_app_instance.widgets["ai_tab"] = {}
    w = main_app_instance.widgets["ai_tab"]

    layout = QVBoxLayout(parent_widget)

    # --- Model Selection Group ---
    model_group = QGroupBox("1. AI Model Configuration")
    model_layout = QFormLayout(model_group)

    w["model_source_selector"] = QComboBox()
    w["model_source_selector"].addItem("Ollama")
    w["model_source_selector"].addItem("Own Trained Model")
    w["ollama_model_label"] = QLabel("Ollama Model:")
    w["ollama_model_selector"] = QComboBox()
    w["refresh_models_button"] = QPushButton("Refresh Models")
    w["refresh_models_button"].clicked.connect(main_app_instance.populate_ollama_models)
    ollama_layout = QHBoxLayout()
    ollama_layout.addWidget(w["ollama_model_selector"])
    ollama_layout.addWidget(w["refresh_models_button"])
    w["model_status_label"] = QLabel("Status: Not Loaded")
    w["load_model_button"] = QPushButton("Load Trained Model")
    model_layout.addRow(QLabel("Model Source:"), w["model_source_selector"])
    model_layout.addRow(w["ollama_model_label"], ollama_layout)
    model_layout.addRow(QLabel("Own Model Status:"), w["model_status_label"])
    model_layout.addRow(w["load_model_button"])
    layout.addWidget(model_group)

    # --- Scan Configuration Group ---
    scan_group = QGroupBox("2. Code Scanning")
    scan_layout = QFormLayout(scan_group)
    w["project_dir_edit"] = QLineEdit()
    w["project_dir_edit"].setText(os.getcwd())
    w["project_dir_edit"].setPlaceholderText("Select a project folder to scan...")
    w["browse_button"] = QPushButton("Browse...")
    w["browse_button"].clicked.connect(main_app_instance.select_scan_directory)
    scan_dir_layout = QHBoxLayout()
    scan_dir_layout.addWidget(w["project_dir_edit"])
    scan_dir_layout.addWidget(w["browse_button"])
    w["include_patterns_edit"] = QLineEdit()
    w["include_patterns_edit"].setText("*.py,*.js,*.ts,*.java,*.cpp,*.c,*.h,*.hpp")
    w["exclude_patterns_edit"] = QLineEdit()
    w["exclude_patterns_edit"].setText(
        "__pycache__/*,node_modules/*,.git/*,*.pyc,*.log"
    )
    scan_layout.addRow(QLabel("Include Patterns:"), w["include_patterns_edit"])
    scan_layout.addRow(QLabel("Exclude Patterns:"), w["exclude_patterns_edit"])
    w["ai_analysis_checkbox"] = QCheckBox("Enable AI-Powered Analysis")
    w["ai_analysis_checkbox"].setChecked(True)
    scan_layout.addRow(w["ai_analysis_checkbox"])
    w["start_scan_button"] = QPushButton("Start Scan")
    w["start_scan_button"].setFixedHeight(35)
    w["start_scan_button"].clicked.connect(main_app_instance.start_scan)
    w["stop_scan_button"] = QPushButton("Stop Scan")
    w["stop_scan_button"].setFixedHeight(35)
    w["stop_scan_button"].setEnabled(False)
    w["stop_scan_button"].clicked.connect(main_app_instance.stop_scan)
    scan_buttons_layout = QHBoxLayout()
    scan_buttons_layout.addWidget(w["start_scan_button"])
    scan_buttons_layout.addWidget(w["stop_scan_button"])
    w["scan_progress_bar"] = QProgressBar()
    w["scan_status_label"] = QLabel("Status: Idle")
    w["scan_status_label"].setAlignment(Qt.AlignmentFlag.AlignCenter)
    scan_layout.addRow(QLabel("Project Directory:"), scan_dir_layout)
    scan_layout.addRow(scan_buttons_layout)
    scan_layout.addRow(w["scan_progress_bar"])
    scan_layout.addRow(w["scan_status_label"])
    layout.addWidget(scan_group)

    # --- Results and Review Group ---
    results_group = QGroupBox("3. Results & Suggestions")
    results_layout = QVBoxLayout(results_group)
    w["scan_results_text"] = QTextEdit()
    w["scan_results_text"].setReadOnly(True)
    w["scan_results_text"].setPlaceholderText("Scan report summary will appear here...")
    w["review_suggestions_button"] = QPushButton("Review Suggestions Interactively")
    w["review_suggestions_button"].setEnabled(False)
    w["review_suggestions_button"].clicked.connect(
        main_app_instance.review_next_suggestion
    )
    w["create_report_button"] = QPushButton("Generate Full Markdown Report")
    w["create_report_button"].setEnabled(False)
    w["create_report_button"].clicked.connect(main_app_instance.start_report_generation)
    # Add enhance_button for AI enhancement
    w["enhance_button"] = QPushButton("Enhance with AI")
    w["enhance_button"].setEnabled(True)
    w["enhance_button"].clicked.connect(main_app_instance.start_ai_enhancement)
    results_layout.addWidget(w["scan_results_text"])
    results_layout.addWidget(w["review_suggestions_button"])
    results_layout.addWidget(w["create_report_button"])
    results_layout.addWidget(w["enhance_button"])
    layout.addWidget(results_group)

    layout.addStretch(1)
