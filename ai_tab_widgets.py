import os
from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel, QGroupBox, QFormLayout, QTextEdit, QFileDialog, QProgressBar, QComboBox)

def setup_ai_tab(parent_widget, main_app_instance):
    layout = QVBoxLayout(parent_widget)

    # NEW: Ollama Model Selection Group
    ollama_group = QGroupBox("2. Enhanced Analysis Configuration")
    ollama_layout = QFormLayout(ollama_group)
    main_app_instance.ollama_model_selector = QComboBox()
    main_app_instance.refresh_ollama_models_button = QPushButton("Refresh Models")
    main_app_instance.refresh_ollama_models_button.clicked.connect(main_app_instance.populate_ollama_models)
    ollama_layout.addRow("Select Ollama Model:", main_app_instance.ollama_model_selector)
    ollama_layout.addRow(main_app_instance.refresh_ollama_models_button)
    layout.addWidget(ollama_group)

    # Code Scanning Group
    scan_group = QGroupBox("1. Scan Code with Local AI")
    scan_layout = QVBoxLayout(scan_group)
    layout.addWidget(scan_group)

    dir_select_layout = QHBoxLayout()
    scan_layout.addLayout(dir_select_layout)
    main_app_instance.scan_dir_entry = QLineEdit(os.path.expanduser("~"))
    dir_select_layout.addWidget(main_app_instance.scan_dir_entry)
    main_app_instance.browse_dir_button = QPushButton("Browse")
    main_app_instance.browse_dir_button.clicked.connect(lambda: _select_directory(main_app_instance.scan_dir_entry))
    dir_select_layout.addWidget(main_app_instance.browse_dir_button)

    main_app_instance.scan_code_button = QPushButton("Scan Python Files")
    main_app_instance.scan_code_button.clicked.connect(lambda: main_app_instance.start_worker('scan_code'))
    scan_layout.addWidget(main_app_instance.scan_code_button) 

    progress_layout = QFormLayout()
    main_app_instance.scan_status_label = QLabel("Ready")
    main_app_instance.scan_progress_bar = QProgressBar()
    progress_layout.addRow("Status:", main_app_instance.scan_status_label)
    progress_layout.addRow("Progress:", main_app_instance.scan_progress_bar)
    scan_layout.addLayout(progress_layout)

    main_app_instance.scan_results_label = QLabel("<b>Scan Results:</b>")
    scan_layout.addWidget(main_app_instance.scan_results_label)
    main_app_instance.scan_results_text = QTextEdit()
    main_app_instance.scan_results_text.setReadOnly(True)
    scan_layout.addWidget(main_app_instance.scan_results_text)

    layout.addStretch(1)

def _select_directory(entry_widget):
    directory = QFileDialog.getExistingDirectory(None, "Select Directory with Python Files")
    if directory:
        entry_widget.setText(directory)