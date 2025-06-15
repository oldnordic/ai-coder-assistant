# data_tab_widgets.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel, QGroupBox,
                             QFormLayout, QLineEdit, QComboBox, QTextEdit)
import config

def setup_data_tab(parent_widget, main_app_instance):
    """
    Sets up the UI components for the data acquisition and model training tab.
    """
    layout = QVBoxLayout(parent_widget)
    
    # --- Data Acquisition Group ---
    acq_group = QGroupBox("1. Data Acquisition")
    acq_layout = QFormLayout(acq_group)

    main_app_instance.doc_urls_input = QTextEdit()
    main_app_instance.doc_urls_input.setPlaceholderText("https://docs.python.org/3/\nhttps://requests.readthedocs.io/en/latest/")
    main_app_instance.doc_urls_input.setMinimumHeight(80)
    main_app_instance.acquire_doc_button = QPushButton("Acquire from URLs")
    
    main_app_instance.github_query_input = QLineEdit("python web scraping")
    main_app_instance.github_token_input = QLineEdit()
    main_app_instance.github_token_input.setEchoMode(QLineEdit.EchoMode.Password)
    main_app_instance.github_token_input.setPlaceholderText("Optional but recommended")
    main_app_instance.acquire_github_button = QPushButton("Acquire from GitHub")

    acq_layout.addRow(QLabel("Documentation URLs (one per line):"), main_app_instance.doc_urls_input)
    acq_layout.addRow(main_app_instance.acquire_doc_button)
    acq_layout.addRow(QLabel("GitHub Search Query:"), main_app_instance.github_query_input)
    acq_layout.addRow(QLabel("GitHub Token:"), main_app_instance.github_token_input)
    acq_layout.addRow(main_app_instance.acquire_github_button)
    
    acq_group.setLayout(acq_layout)
    layout.addWidget(acq_group)

    # --- Local Data and Pre-processing Group ---
    pre_proc_group = QGroupBox("2. Pre-process All Data")
    pre_proc_layout = QVBoxLayout(pre_proc_group)

    main_app_instance.add_local_files_button = QPushButton("Add Local Docs/Transcripts to Corpus")
    main_app_instance.local_files_label = QLabel("No local folder added yet.")
    
    main_app_instance.knowledge_mode_selector = QComboBox()
    main_app_instance.knowledge_mode_selector.addItem("Reset Knowledge (Overwrite All)")
    main_app_instance.knowledge_mode_selector.addItem("Accumulate Knowledge (Add New)")
    
    main_app_instance.preprocess_docs_button = QPushButton("Pre-process All Docs & Feedback")

    pre_proc_layout.addWidget(main_app_instance.add_local_files_button)
    pre_proc_layout.addWidget(main_app_instance.local_files_label)
    pre_proc_layout.addWidget(QLabel("Knowledge Mode:"))
    pre_proc_layout.addWidget(main_app_instance.knowledge_mode_selector)
    pre_proc_layout.addWidget(main_app_instance.preprocess_docs_button)
    layout.addWidget(pre_proc_group)

    # --- Training Group ---
    train_lm_group = QGroupBox("3. Model Training")
    train_lm_layout = QVBoxLayout(train_lm_group)

    main_app_instance.train_lm_button = QPushButton("Train Base Model from Corpus")
    main_app_instance.finetune_lm_button = QPushButton("Finetune Model with Feedback")
    
    train_lm_layout.addWidget(main_app_instance.train_lm_button)
    train_lm_layout.addWidget(main_app_instance.finetune_lm_button)
    layout.addWidget(train_lm_group)

    layout.addStretch(1)