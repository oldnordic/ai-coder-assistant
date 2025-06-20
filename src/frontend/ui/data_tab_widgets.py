"""
data_tab_widgets.py

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

# src/frontend/ui/data_tab_widgets.py
from PyQt6.QtWidgets import (QVBoxLayout, QPushButton, QLabel, QGroupBox,
                             QTextEdit, QComboBox, QHBoxLayout, QSpinBox, QCheckBox)
from backend.utils.constants import (
    INPUT_HEIGHT, DEFAULT_MAX_PAGES_SPINBOX_VALUE, DEFAULT_MAX_DEPTH_SPINBOX_VALUE,
    DEFAULT_LINKS_PER_PAGE_SPINBOX_VALUE,
    MAX_PAGES_SPINBOX_RANGE, MAX_DEPTH_SPINBOX_RANGE, MAX_LINKS_PER_PAGE_SPINBOX_RANGE
)

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
    main_app_instance.add_local_files_button.clicked.connect(main_app_instance.select_local_corpus_dir)
    main_app_instance.local_files_label = QLabel("No local folder selected.")
    acq_layout.addWidget(main_app_instance.add_local_files_button)
    acq_layout.addWidget(main_app_instance.local_files_label)

    acq_layout.addWidget(QLabel("\nScrape documents from web URLs (one URL per line):"))
    main_app_instance.doc_urls_input = QTextEdit()
    main_app_instance.doc_urls_input.setPlaceholderText("https://example.com/article1\nhttps://anothersite.org/page")
    main_app_instance.doc_urls_input.setFixedHeight(INPUT_HEIGHT)
    acq_layout.addWidget(main_app_instance.doc_urls_input)
    
    # Enhanced scraping options
    scraping_options_layout = QHBoxLayout()
    
    # Scraping mode selector
    scraping_mode_layout = QVBoxLayout()
    scraping_mode_layout.addWidget(QLabel("Scraping Mode:"))
    main_app_instance.scraping_mode_selector = QComboBox()
    main_app_instance.scraping_mode_selector.addItem("Enhanced (Follow Links)")
    main_app_instance.scraping_mode_selector.addItem("Simple (Single Page)")
    main_app_instance.scraping_mode_selector.setCurrentIndex(0)
    scraping_mode_layout.addWidget(main_app_instance.scraping_mode_selector)
    scraping_options_layout.addLayout(scraping_mode_layout)
    
    # Enhanced scraping parameters
    enhanced_params_layout = QVBoxLayout()
    enhanced_params_layout.addWidget(QLabel("Enhanced Parameters:"))
    
    # Max pages
    max_pages_layout = QHBoxLayout()
    max_pages_layout.addWidget(QLabel("Max Pages:"))
    main_app_instance.max_pages_spinbox = QSpinBox()
    main_app_instance.max_pages_spinbox.setRange(1, MAX_PAGES_SPINBOX_RANGE)
    main_app_instance.max_pages_spinbox.setValue(DEFAULT_MAX_PAGES_SPINBOX_VALUE)
    main_app_instance.max_pages_spinbox.setToolTip("Maximum number of pages to scrape per URL")
    max_pages_layout.addWidget(main_app_instance.max_pages_spinbox)
    enhanced_params_layout.addLayout(max_pages_layout)
    
    # Max depth
    max_depth_layout = QHBoxLayout()
    max_depth_layout.addWidget(QLabel("Max Depth:"))
    main_app_instance.max_depth_spinbox = QSpinBox()
    main_app_instance.max_depth_spinbox.setRange(1, MAX_DEPTH_SPINBOX_RANGE)
    main_app_instance.max_depth_spinbox.setValue(DEFAULT_MAX_DEPTH_SPINBOX_VALUE)
    main_app_instance.max_depth_spinbox.setToolTip("Maximum depth to follow links")
    max_depth_layout.addWidget(main_app_instance.max_depth_spinbox)
    enhanced_params_layout.addLayout(max_depth_layout)
    
    # Same domain only
    main_app_instance.same_domain_checkbox = QCheckBox("Same Domain Only")
    main_app_instance.same_domain_checkbox.setChecked(True)
    main_app_instance.same_domain_checkbox.setToolTip("Only follow links within the same domain")
    enhanced_params_layout.addWidget(main_app_instance.same_domain_checkbox)
    
    # Links per page
    links_per_page_layout = QHBoxLayout()
    links_per_page_layout.addWidget(QLabel("Links per page:"))
    main_app_instance.links_per_page_spinbox = QSpinBox()
    main_app_instance.links_per_page_spinbox.setRange(1, MAX_LINKS_PER_PAGE_SPINBOX_RANGE)
    main_app_instance.links_per_page_spinbox.setValue(DEFAULT_LINKS_PER_PAGE_SPINBOX_VALUE)
    main_app_instance.links_per_page_spinbox.setToolTip("Maximum number of links to follow per page")
    links_per_page_layout.addWidget(main_app_instance.links_per_page_spinbox)
    enhanced_params_layout.addLayout(links_per_page_layout)
    
    scraping_options_layout.addLayout(enhanced_params_layout)
    acq_layout.addLayout(scraping_options_layout)
    
    main_app_instance.acquire_doc_button = QPushButton("Scrape URLs and Add to Corpus")
    main_app_instance.acquire_doc_button.clicked.connect(main_app_instance.start_doc_acquisition)
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
    main_app_instance.preprocess_docs_button.clicked.connect(main_app_instance.start_preprocessing)
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
    main_app_instance.train_lm_button.clicked.connect(main_app_instance.start_base_training)
    main_app_instance.finetune_lm_button = QPushButton("Finetune Model with Feedback")
    main_app_instance.finetune_lm_button.setToolTip(
        "Continues training the existing model on the high-quality examples\n"
        "from your feedback and the reports."
    )
    main_app_instance.finetune_lm_button.clicked.connect(main_app_instance.start_finetuning)
    train_lm_layout.addWidget(main_app_instance.train_lm_button)
    train_lm_layout.addWidget(main_app_instance.finetune_lm_button)
    layout.addWidget(train_lm_group)
    
    main_app_instance.acquire_github_button = QPushButton("Acquire from GitHub")
    main_app_instance.acquire_github_button.setVisible(False)

    layout.addStretch(1)