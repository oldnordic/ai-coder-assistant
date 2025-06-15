# data_tab_widgets.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel, QGroupBox, QProgressBar, QFormLayout, QLineEdit, QComboBox)
import config

def setup_data_tab(parent_widget, main_app_instance):
    """
    Sets up the UI components for the data acquisition and preprocessing tab.
    """
    layout = QVBoxLayout(parent_widget)
    
    acq_group = QGroupBox("1. Acquire Documentation from Web")
    acq_layout = QFormLayout(acq_group)
    
    main_app_instance.doc_language_selector = QComboBox()
    languages = list(config.DOCUMENTATION_SOURCES.keys())
    main_app_instance.doc_language_selector.addItems(languages)
    acq_layout.addRow("Select Language:", main_app_instance.doc_language_selector)
    
    main_app_instance.acquire_doc_button = QPushButton("Start Acquisition")
    acq_layout.addRow(main_app_instance.acquire_doc_button)
    
    main_app_instance.acquire_doc_status_label = QLabel("Ready")
    main_app_instance.acquire_doc_progressbar = QProgressBar()
    acq_layout.addRow("Status:", main_app_instance.acquire_doc_status_label)
    acq_layout.addRow("Progress:", main_app_instance.acquire_doc_progressbar)
    layout.addWidget(acq_group)

    github_group = QGroupBox("2. Acquire Code from GitHub")
    github_layout = QFormLayout(github_group)
    main_app_instance.github_token_entry = QLineEdit()
    main_app_instance.github_token_entry.setEchoMode(QLineEdit.EchoMode.Password)
    main_app_instance.github_query_entry = QLineEdit("python language:python")
    github_layout.addRow("GitHub Token:", main_app_instance.github_token_entry)
    github_layout.addRow("Search Query:", main_app_instance.github_query_entry)
    main_app_instance.acquire_github_button = QPushButton("Acquire from GitHub")
    github_layout.addRow(main_app_instance.acquire_github_button)
    main_app_instance.github_status_label = QLabel("Ready")
    main_app_instance.github_progressbar = QProgressBar()
    github_layout.addRow("Status:", main_app_instance.github_status_label)
    github_layout.addRow("Progress:", main_app_instance.github_progressbar)
    layout.addWidget(github_group)

    pre_proc_group = QGroupBox("3. Pre-process All Docs for AI")
    pre_proc_layout = QVBoxLayout(pre_proc_group)

    main_app_instance.knowledge_mode_selector = QComboBox()
    main_app_instance.knowledge_mode_selector.addItem("Reset Knowledge (Overwrite)")
    main_app_instance.knowledge_mode_selector.addItem("Accumulate Knowledge (Add New)")
    main_app_instance.knowledge_mode_selector.setCurrentText("Accumulate Knowledge (Add New)")
    pre_proc_layout.addWidget(QLabel("Knowledge Mode:"))
    pre_proc_layout.addWidget(main_app_instance.knowledge_mode_selector)

    main_app_instance.add_local_files_button = QPushButton("Add Local Folder to Corpus")
    pre_proc_layout.addWidget(main_app_instance.add_local_files_button)
    main_app_instance.local_files_label = QLabel("No local folder added yet.")
    pre_proc_layout.addWidget(main_app_instance.local_files_label)
    main_app_instance.preprocess_docs_button = QPushButton("Start Pre-processing")
    pre_proc_layout.addWidget(main_app_instance.preprocess_docs_button)
    main_app_instance.preprocess_docs_status_label = QLabel("Ready")
    main_app_instance.preprocess_docs_progressbar = QProgressBar()
    form_layout_preprocess = QFormLayout()
    form_layout_preprocess.addRow("Status:", main_app_instance.preprocess_docs_status_label)
    form_layout_preprocess.addRow("Progress:", main_app_instance.preprocess_docs_progressbar)
    pre_proc_layout.addLayout(form_layout_preprocess)
    layout.addWidget(pre_proc_group)

    train_lm_group = QGroupBox("4. Train AI Language Model")
    train_lm_layout = QFormLayout(train_lm_group)
    main_app_instance.train_lm_button = QPushButton("Start Training")
    train_lm_layout.addRow(main_app_instance.train_lm_button)
    main_app_instance.train_lm_status_label = QLabel("Ready")
    main_app_instance.train_lm_progressbar = QProgressBar()
    train_lm_layout.addRow("Status:", main_app_instance.train_lm_status_label)
    train_lm_layout.addRow("Progress:", main_app_instance.train_lm_progressbar)
    layout.addWidget(train_lm_group)
    
    layout.addStretch(1)