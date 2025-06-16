# src/ui/browser_tab.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLineEdit, QGroupBox, QTextEdit, QLabel)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl

"""UI widgets for the embedded browser and YouTube transcription panel."""

def setup_browser_tab(parent_widget, main_app_instance):
    """
    Sets up the UI components for the browser and YouTube transcription tab.
    """
    layout = QVBoxLayout(parent_widget)

    # --- Browser Group ---
    browser_group = QGroupBox("Web Browser")
    browser_layout = QVBoxLayout(browser_group)

    url_layout = QHBoxLayout()
    main_app_instance.url_bar = QLineEdit()
    main_app_instance.url_bar.setPlaceholderText("https://www.google.com")
    
    # --- FIXED: Correctly assign the button to the main app instance ---
    main_app_instance.go_button = QPushButton("Go")
    
    url_layout.addWidget(main_app_instance.url_bar)
    url_layout.addWidget(main_app_instance.go_button)
    
    main_app_instance.browser = QWebEngineView()
    main_app_instance.browser.setUrl(QUrl("https://www.google.com"))

    browser_layout.addLayout(url_layout)
    browser_layout.addWidget(main_app_instance.browser)
    layout.addWidget(browser_group)

    # --- YouTube Transcription Group ---
    yt_group = QGroupBox("YouTube Transcription")
    yt_layout = QVBoxLayout(yt_group)

    yt_url_layout = QHBoxLayout()
    yt_url_layout.addWidget(QLabel("YouTube URL:"))
    main_app_instance.youtube_url_entry = QLineEdit()
    yt_url_layout.addWidget(main_app_instance.youtube_url_entry)
    
    main_app_instance.transcribe_button = QPushButton("Transcribe Video Audio")
    
    main_app_instance.transcription_results_text = QTextEdit()
    main_app_instance.transcription_results_text.setReadOnly(True)
    main_app_instance.transcription_results_text.setPlaceholderText("Transcription will appear here...")

    yt_layout.addLayout(yt_url_layout)
    yt_layout.addWidget(main_app_instance.transcribe_button)
    yt_layout.addWidget(main_app_instance.transcription_results_text)
    layout.addWidget(yt_group)

    layout.setStretchFactor(browser_group, 2)
    layout.setStretchFactor(yt_group, 1)
