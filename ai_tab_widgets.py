# ai_tab_widgets.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGroupBox,
    QProgressBar, QFormLayout, QLineEdit, QFileDialog, QTextEdit, QComboBox
)
import config

def setup_ai_tab(parent_widget, main_app_instance):
    """
    Sets up the UI components for the AI code analysis tab.
    """
    layout = QVBoxLayout(parent_widget)
    
    # --- Enhanced Analysis Configuration ---
    ollama_group = QGroupBox("1. Enhanced Analysis Configuration")
    ollama_layout = QFormLayout(ollama_group)
    
    main_app_instance.ollama_model_selector = QComboBox()
    refresh_button = QPushButton("Refresh Models")
    refresh_button.setObjectName("Refresh Models")
    ollama_layout.addRow("Select Ollama Model:", main_app_instance.ollama_model_selector)
    ollama_layout.addRow(refresh_button)

    main_app_instance.model_source_selector = QComboBox()
    main_app_instance.model_source_selector.addItem("Use Ollama Model")
    main_app_instance.model_source_selector.addItem("Use Own Trained Model")
    main_app_instance.model_source_selector.currentIndexChanged.connect(main_app_instance.on_model_source_changed)
    ollama_layout.addRow("Select AI Source:", main_app_instance.model_source_selector)
    layout.addWidget(ollama_group)

    # --- Code Scanning ---
    scan_group = QGroupBox("2. Scan Project")
    scan_layout = QVBoxLayout(scan_group)
    
    dir_layout = QHBoxLayout()
    main_app_instance.scan_dir_entry = QLineEdit()
    main_app_instance.scan_dir_entry.setPlaceholderText("Select a project directory to scan...")
    browse_button = QPushButton("Browse")
    browse_button.setObjectName("Browse")
    
    dir_layout.addWidget(main_app_instance.scan_dir_entry)
    dir_layout.addWidget(browse_button)
    scan_layout.addLayout(dir_layout)
    
    main_app_instance.scan_button = QPushButton("Scan Project Files")
    scan_layout.addWidget(main_app_instance.scan_button)
    
    progress_layout = QFormLayout()
    main_app_instance.scan_status_label = QLabel("Ready")
    main_app_instance.scan_progress_bar = QProgressBar()
    progress_layout.addRow("Status:", main_app_instance.scan_status_label)
    progress_layout.addRow("Progress:", main_app_instance.scan_progress_bar)
    scan_layout.addLayout(progress_layout)
    layout.addWidget(scan_group)

    # --- Scan Report and Suggestions ---
    results_group = QGroupBox("3. Scan Report & Suggestions")
    results_layout = QVBoxLayout(results_group)
    main_app_instance.scan_results_text = QTextEdit()
    main_app_instance.scan_results_text.setReadOnly(True)
    main_app_instance.scan_results_text.setPlaceholderText("Scan report will be displayed here.")
    results_layout.addWidget(main_app_instance.scan_results_text)
    
    action_buttons_layout = QHBoxLayout()
    main_app_instance.review_suggestions_button = QPushButton("Review Suggestions")
    main_app_instance.review_suggestions_button.setEnabled(False) 
    
    main_app_instance.create_report_button = QPushButton("Create Report")
    main_app_instance.create_report_button.setEnabled(False)

    action_buttons_layout.addWidget(main_app_instance.review_suggestions_button)
    action_buttons_layout.addWidget(main_app_instance.create_report_button)
    results_layout.addLayout(action_buttons_layout)
    
    layout.addWidget(results_group)
    layout.addStretch(1)