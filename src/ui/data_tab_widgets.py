# src/ui/data_tab_widgets.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel, QGroupBox,
                             QTextEdit, QComboBox)
from ..config import settings

def setup_data_tab(parent_widget, main_app_instance):
    """
    Sets up the UI components for the data acquisition and model training tab.
    """
    layout = QVBoxLayout(parent_widget)
    
    # --- Data Management Group ---
    acq_group = QGroupBox("1. Data Acquisition")
    acq_layout = QVBoxLayout(acq_group)
    
    acq_layout.addWidget(QLabel("Add documents from local folder:"))
    main_app_instance.add_local_files_button = QPushButton("Select Local Docs Folder")
    main_app_instance.local_files_label = QLabel("No local folder selected.")
    acq_layout.addWidget(main_app_instance.add_local_files_button)
    acq_layout.addWidget(main_app_instance.local_files_label)

    acq_layout.addWidget(QLabel("\nScrape documents from web URLs (one URL per line):"))
    main_app_instance.doc_urls_input = QTextEdit()
    main_app_instance.doc_urls_input.setPlaceholderText("https://example.com/article1\nhttps://anothersite.org/page")
    main_app_instance.doc_urls_input.setFixedHeight(100)
    acq_layout.addWidget(main_app_instance.doc_urls_input)
    
    main_app_instance.acquire_doc_button = QPushButton("Scrape URLs and Add to Corpus")
    acq_layout.addWidget(main_app_instance.acquire_doc_button)
    
    layout.addWidget(acq_group)

    # --- Pre-processing Group ---
    pre_proc_group = QGroupBox("2. Pre-process All Data")
    pre_proc_layout = QVBoxLayout(pre_proc_group)

    main_app_instance.knowledge_mode_selector = QComboBox()
    main_app_instance.knowledge_mode_selector.addItem("Reset and Re-process All")
    main_app_instance.knowledge_mode_selector.addItem("Accumulate New Data")
    main_app_instance.knowledge_mode_selector.setCurrentIndex(1)
    pre_proc_layout.addWidget(QLabel("Processing Mode:"))
    pre_proc_layout.addWidget(main_app_instance.knowledge_mode_selector)

    main_app_instance.preprocess_docs_button = QPushButton("Pre-process All Docs & Feedback")
    main_app_instance.preprocess_docs_button.setToolTip(
        "Processes docs for the knowledge base and prepares all data for training."
    )
    pre_proc_layout.addWidget(main_app_instance.preprocess_docs_button)
    layout.addWidget(pre_proc_group)

    # --- Training Group ---
    train_lm_group = QGroupBox("3. Model Training")
    train_lm_layout = QVBoxLayout(train_lm_group)

    main_app_instance.train_lm_button = QPushButton("Train Base Model from Corpus")
    main_app_instance.train_lm_button.setToolTip(
        "Trains the model from scratch on the general documentation corpus.\n"
        "Run this once, or after adding significant new documentation."
    )
    main_app_instance.finetune_lm_button = QPushButton("Finetune Model with Feedback")
    main_app_instance.finetune_lm_button.setToolTip(
        "Continues training the existing model on the high-quality examples\n"
        "from your feedback and the reports."
    )
    train_lm_layout.addWidget(main_app_instance.train_lm_button)
    train_lm_layout.addWidget(main_app_instance.finetune_lm_button)
    layout.addWidget(train_lm_group)
    
    main_app_instance.acquire_github_button = QPushButton("Acquire from GitHub")
    main_app_instance.acquire_github_button.setVisible(False)

    layout.addStretch(1)