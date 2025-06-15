# ai_tab_widgets.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGroupBox,
                             QProgressBar, QFormLayout, QLineEdit, QComboBox, QTextEdit)
from PyQt6.QtCore import Qt

def setup_ai_tab(parent_widget, main_app_instance):
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
    
    # --- Ollama Widgets ---
    main_app_instance.ollama_model_label = QLabel("Ollama Model:")
    main_app_instance.ollama_model_selector = QComboBox()
    main_app_instance.refresh_button = QPushButton("Refresh Models")
    ollama_layout = QHBoxLayout()
    ollama_layout.addWidget(main_app_instance.ollama_model_selector)
    ollama_layout.addWidget(main_app_instance.refresh_button)

    # --- Own Model Widgets (FIXED) ---
    main_app_instance.model_status_label = QLabel("Status: Not Loaded")
    main_app_instance.load_model_button = QPushButton("Load Trained Model")

    # Add widgets to layout
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
    
    scan_dir_layout = QHBoxLayout()
    scan_dir_layout.addWidget(main_app_instance.scan_dir_entry)
    scan_dir_layout.addWidget(main_app_instance.browse_button)
    
    main_app_instance.scan_button = QPushButton("Start Scan")
    main_app_instance.scan_button.setFixedHeight(35)
    
    main_app_instance.scan_progress_bar = QProgressBar()
    main_app_instance.scan_status_label = QLabel("Status: Idle")
    main_app_instance.scan_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    scan_layout.addRow(QLabel("Project Directory:"), scan_dir_layout)
    scan_layout.addRow(main_app_instance.scan_button)
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
    
    main_app_instance.create_report_button = QPushButton("Generate Full HTML Report")
    main_app_instance.create_report_button.setEnabled(False)

    results_layout.addWidget(main_app_instance.scan_results_text)
    results_layout.addWidget(main_app_instance.review_suggestions_button)
    results_layout.addWidget(main_app_instance.create_report_button)
    layout.addWidget(results_group)

    layout.addStretch(1)