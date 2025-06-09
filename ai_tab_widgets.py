import os
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel, QGroupBox, QFormLayout, QTextEdit, QFileDialog, QProgressBar

def setup_ai_tab(parent_widget, main_app_instance):
    layout = QVBoxLayout(parent_widget)

    # 1. Code Scanning & Error Justification Section
    scan_group = QGroupBox("1. Scan Code for Errors & Justification")
    scan_layout = QVBoxLayout(scan_group)
    layout.addWidget(scan_group)

    # Directory selection
    dir_select_layout = QHBoxLayout()
    scan_layout.addLayout(dir_select_layout)
    main_app_instance.scan_dir_entry = QLineEdit(os.path.expanduser("~"))
    dir_select_layout.addWidget(main_app_instance.scan_dir_entry)
    main_app_instance.browse_dir_button = QPushButton("Browse")
    main_app_instance.browse_dir_button.clicked.connect(lambda: _select_directory(main_app_instance.scan_dir_entry))
    dir_select_layout.addWidget(main_app_instance.browse_dir_button)

    # Scan button
    main_app_instance.scan_code_button = QPushButton("Scan Python Files")
    main_app_instance.scan_code_button.clicked.connect(lambda: main_app_instance.start_worker('scan_code'))
    scan_layout.addWidget(main_app_instance.scan_code_button) 

    # NEW: Progress bar and status label for scanning
    progress_layout = QFormLayout()
    main_app_instance.scan_status_label = QLabel("Ready")
    main_app_instance.scan_progress_bar = QProgressBar()
    progress_layout.addRow("Status:", main_app_instance.scan_status_label)
    progress_layout.addRow("Progress:", main_app_instance.scan_progress_bar)
    scan_layout.addLayout(progress_layout)

    # Scan results display
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