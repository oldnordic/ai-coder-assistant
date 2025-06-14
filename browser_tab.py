# browser_tab.py
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QGroupBox, QFormLayout, QTextEdit, QLabel, QProgressBar) # Added QLabel and QProgressBar
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6.QtCore import QUrl

def setup_browser_tab(parent_widget, main_app_instance, browser_profile):
    """
    Sets up the UI components for the embedded browser tab.
    """
    layout = QVBoxLayout(parent_widget)

    # URL Navigation bar
    nav_bar_layout = QHBoxLayout()
    main_app_instance.url_bar = QLineEdit()
    main_app_instance.url_bar.returnPressed.connect(main_app_instance.navigate_to_url)
    
    back_button = QPushButton("<")
    forward_button = QPushButton(">") # Corrected: Removed " discontent"
    reload_button = QPushButton("Reload")

    nav_bar_layout.addWidget(back_button)
    nav_bar_layout.addWidget(forward_button)
    nav_bar_layout.addWidget(reload_button)
    nav_bar_layout.addWidget(main_app_instance.url_bar)
    layout.addLayout(nav_bar_layout)

    # Create Browser View with Persistent Profile
    main_app_instance.browser = QWebEngineView()
    page = QWebEnginePage(browser_profile, main_app_instance.browser)
    main_app_instance.browser.setPage(page)
    main_app_instance.browser.setUrl(QUrl("https://www.google.com"))

    # Connect Signals
    back_button.clicked.connect(main_app_instance.browser.back)
    forward_button.clicked.connect(main_app_instance.browser.forward)
    reload_button.clicked.connect(main_app_instance.browser.reload)
    main_app_instance.browser.urlChanged.connect(main_app_instance.update_url_bar)
    
    layout.addWidget(main_app_instance.browser)

    # YouTube Transcription Group
    transcription_group = QGroupBox("YouTube Transcription")
    transcription_layout = QFormLayout(transcription_group)
    main_app_instance.youtube_url_entry = QLineEdit()
    main_app_instance.youtube_url_entry.setPlaceholderText("Paste a YouTube URL here...")
    main_app_instance.transcribe_button = QPushButton("Transcribe YouTube URL")
    main_app_instance.transcribe_button.clicked.connect(main_app_instance.start_youtube_transcription)
    main_app_instance.transcription_results_text = QTextEdit()
    main_app_instance.transcription_results_text.setReadOnly(True)
    main_app_instance.transcription_results_text.setPlaceholderText("Transcription results will appear here...")
    
    # NEW: Add a specific progress bar and status label for transcription
    main_app_instance.transcription_status_label = QLabel("Ready") # Status label
    main_app_instance.transcription_progressbar = QProgressBar() # Progress bar
    main_app_instance.transcription_progressbar.setValue(0) # Initialize to 0%
    main_app_instance.transcription_progressbar.setTextVisible(True) # Make percentage visible

    transcription_layout.addRow("YouTube URL:", main_app_instance.youtube_url_entry)
    transcription_layout.addRow(main_app_instance.transcribe_button)
    transcription_layout.addRow("Status:", main_app_instance.transcription_status_label) # Add status label to layout
    transcription_layout.addRow("Progress:", main_app_instance.transcription_progressbar) # Add progress bar to layout
    transcription_layout.addRow("Results:", main_app_instance.transcription_results_text)
    
    layout.addWidget(transcription_group)