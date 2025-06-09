import os
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGroupBox, 
    QProgressBar, QFormLayout
)

def setup_data_tab(parent_widget, main_app_instance):
    """
    Sets up the UI components for the data acquisition and preprocessing tab.
    """
    layout = QVBoxLayout(parent_widget)
    
    # --- 1. Documentation Acquisition ---
    acq_group = QGroupBox("1. Acquire Documentation from Web")
    acq_layout = QVBoxLayout(acq_group)
    
    main_app_instance.acquire_doc_button = QPushButton("Start Acquisition")
    # CORRECTED: Pass a string identifier instead of a function reference.
    main_app_instance.acquire_doc_button.clicked.connect(
        lambda: main_app_instance.start_worker('acquire_doc')
    )
    acq_layout.addWidget(main_app_instance.acquire_doc_button)
    
    acq_progress_layout = QFormLayout()
    main_app_instance.acquire_doc_status_label = QLabel("Ready")
    main_app_instance.acquire_doc_progressbar = QProgressBar()
    acq_progress_layout.addRow("Status:", main_app_instance.acquire_doc_status_label)
    acq_progress_layout.addRow("Progress:", main_app_instance.acquire_doc_progressbar)
    acq_layout.addLayout(acq_progress_layout)
    
    layout.addWidget(acq_group)

    # --- 2. Pre-process Documentation ---
    pre_proc_group = QGroupBox("2. Pre-process Docs for AI")
    pre_proc_layout = QVBoxLayout(pre_proc_group)

    main_app_instance.preprocess_docs_button = QPushButton("Start Pre-processing")
    main_app_instance.preprocess_docs_button.clicked.connect(
        lambda: main_app_instance.start_worker('preprocess_docs')
    )
    pre_proc_layout.addWidget(main_app_instance.preprocess_docs_button)

    pre_proc_progress_layout = QFormLayout()
    main_app_instance.preprocess_docs_status_label = QLabel("Ready")
    main_app_instance.preprocess_docs_progressbar = QProgressBar()
    pre_proc_progress_layout.addRow("Status:", main_app_instance.preprocess_docs_status_label)
    pre_proc_progress_layout.addRow("Progress:", main_app_instance.preprocess_docs_progressbar)
    pre_proc_layout.addLayout(pre_proc_progress_layout)

    layout.addWidget(pre_proc_group)

    # --- 3. Train Language Model ---
    train_lm_group = QGroupBox("3. Train AI Language Model")
    train_lm_layout = QVBoxLayout(train_lm_group)

    main_app_instance.train_lm_button = QPushButton("Start Training")
    main_app_instance.train_lm_button.clicked.connect(
        lambda: main_app_instance.start_worker('train_lm')
    )
    train_lm_layout.addWidget(main_app_instance.train_lm_button)

    train_lm_progress_layout = QFormLayout()
    main_app_instance.train_lm_status_label = QLabel("Ready")
    main_app_instance.train_lm_progressbar = QProgressBar()
    train_lm_progress_layout.addRow("Status:", main_app_instance.train_lm_status_label)
    train_lm_progress_layout.addRow("Progress:", main_app_instance.train_lm_progressbar)
    train_lm_layout.addLayout(train_lm_progress_layout)

    layout.addWidget(train_lm_group)
    
    layout.addStretch(1)