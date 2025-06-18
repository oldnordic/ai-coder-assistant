"""
markdown_viewer.py

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

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTextBrowser, QLabel, QLineEdit, QComboBox,
                             QDialogButtonBox, QProgressBar, QSplitter)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor, QTextCharFormat, QColor
import re
import os
from ...backend.utils.constants import (
    WINDOW_DEFAULT_X, WINDOW_DEFAULT_Y, WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT,
    DIALOG_DEFAULT_WIDTH, DIALOG_DEFAULT_HEIGHT, 
    LOG_CONSOLE_MAX_HEIGHT, DEFAULT_BACKGROUND_COLOR, DEFAULT_FOREGROUND_COLOR, DEFAULT_BORDER_COLOR
)
from ...utils.constants import DEFAULT_FONT_WEIGHT, DEFAULT_TEXT_COLOR

class MarkdownRenderer:
    """Simple markdown to HTML renderer for the viewer."""
    
    @staticmethod
    def render_markdown(markdown_text: str) -> str:
        """Convert markdown to HTML for display."""
        html = markdown_text
        
        # Headers
        html = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        
        # Bold and italic
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
        
        # Code blocks
        html = re.sub(r'```(\w+)?\n(.*?)\n```', r'<pre><code class="\1">\2</code></pre>', html, flags=re.DOTALL)
        html = re.sub(r'`(.*?)`', r'<code>\1</code>', html)
        
        # Links
        html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)
        
        # Lists
        html = re.sub(r'^- (.*?)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        html = re.sub(r'(\n<li>.*?</li>\n)+', r'<ul>\g<0></ul>', html, flags=re.DOTALL)
        
        # Line breaks
        html = html.replace('\n\n', '</p><p>')
        html = html.replace('\n', '<br>')
        
        # Wrap in proper HTML structure
        html = f"""
        <html>
        <head>
            <style>
                body {{ 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Noto Sans', sans-serif; 
                    line-height: 1.7; 
                    margin: 20px; 
                    background-color: #ffffff; 
                    color: #2c3e50;
                    font-size: 14px;
                }}
                h1 {{ 
                    color: #1a252f; 
                    border-bottom: 3px solid #3498db; 
                    padding-bottom: 10px; 
                    font-size: 28px;
                    margin-top: 30px;
                    margin-bottom: 20px;
                }}
                h2 {{ 
                    color: #2c3e50; 
                    border-bottom: 2px solid #bdc3c7; 
                    padding-bottom: 8px; 
                    font-size: 24px;
                    margin-top: 25px;
                    margin-bottom: 15px;
                }}
                h3 {{ 
                    color: #34495e; 
                    font-size: 20px;
                    margin-top: 20px;
                    margin-bottom: 10px;
                }}
                p {{
                    margin-bottom: 15px;
                    color: #2c3e50;
                }}
                code {{ 
                    background-color: #f8f9fa; 
                    color: #e74c3c;
                    padding: 3px 6px; 
                    border-radius: 4px; 
                    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                    font-size: 13px;
                    border: 1px solid #e9ecef;
                }}
                pre {{ 
                    background-color: #2c3e50; 
                    color: #ecf0f1; 
                    padding: 20px; 
                    border-radius: 8px; 
                    overflow-x: auto;
                    border: 1px solid #34495e;
                    margin: 15px 0;
                }}
                pre code {{ 
                    background-color: transparent; 
                    padding: 0; 
                    color: #ecf0f1;
                    border: none;
                }}
                ul {{ 
                    padding-left: 25px; 
                    margin-bottom: 15px;
                }}
                li {{ 
                    margin-bottom: 8px; 
                    color: #2c3e50;
                }}
                a {{ 
                    color: #2980b9; 
                    text-decoration: none; 
                    font-weight: {DEFAULT_FONT_WEIGHT};
                }}
                a:hover {{ 
                    text-decoration: underline; 
                    color: #3498db;
                }}
                .issue-section {{ 
                    background-color: #f8f9fa; 
                    padding: 20px; 
                    margin: 15px 0; 
                    border-radius: 8px; 
                    border-left: 5px solid #3498db;
                    border: 1px solid #e9ecef;
                }}
                .critical {{ 
                    border-left-color: #e74c3c; 
                    background-color: #fdf2f2;
                }}
                .high {{ 
                    border-left-color: #f39c12; 
                    background-color: #fef9e7;
                }}
                .medium {{ 
                    border-left-color: #f1c40f; 
                    background-color: #fefce8;
                }}
                .low {{ 
                    border-left-color: #27ae60; 
                    background-color: #f0f9f4;
                }}
                .summary {{
                    background-color: #e8f4fd;
                    padding: 15px;
                    border-radius: 6px;
                    border: 1px solid #bee5eb;
                    margin: 15px 0;
                }}
                .recommendation {{
                    background-color: #fff3cd;
                    padding: 15px;
                    border-radius: 6px;
                    border: 1px solid #ffeaa7;
                    margin: 15px 0;
                }}
                .file-path {{
                    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                    background-color: #f8f9fa;
                    padding: 4px 8px;
                    border-radius: 4px;
                    color: #{DEFAULT_TEXT_COLOR};
                    font-size: 12px;
                }}
                .severity-high {{
                    color: #e74c3c;
                    font-weight: bold;
                }}
                .severity-medium {{
                    color: #f39c12;
                    font-weight: bold;
                }}
                .severity-low {{
                    color: #27ae60;
                    font-weight: bold;
                }}
                .severity-critical {{
                    color: #c0392b;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <p>{html}</p>
        </body>
        </html>
        """
        
        return html

class MarkdownViewerDialog(QDialog):
    def __init__(self, markdown_content: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI Code Review Report - Markdown Viewer")
        self.setGeometry(WINDOW_DEFAULT_X, WINDOW_DEFAULT_Y, WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT)
        self.markdown_content = markdown_content
        
        # Setup UI
        self.setup_ui()
        self.render_markdown()
        
    def setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        # Search functionality
        self.search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter search term...")
        self.search_input.textChanged.connect(self.search_text)
        
        # Search options
        self.search_options = QComboBox()
        self.search_options.addItems(["Case Sensitive", "Case Insensitive"])
        
        # Navigation buttons
        self.prev_button = QPushButton("Previous")
        self.prev_button.clicked.connect(self.find_previous)
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.find_next)
        
        toolbar.addWidget(self.search_label)
        toolbar.addWidget(self.search_input)
        toolbar.addWidget(self.search_options)
        toolbar.addWidget(self.prev_button)
        toolbar.addWidget(self.next_button)
        toolbar.addStretch()
        
        # Progress indicator
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        toolbar.addWidget(self.progress_bar)
        
        layout.addLayout(toolbar)
        
        # Main content area
        self.content_browser = QTextBrowser()
        self.content_browser.setOpenExternalLinks(True)
        self.content_browser.setFont(QFont("Segoe UI", 12))  # Larger, more readable font
        self.content_browser.setStyleSheet("""
            QTextBrowser {
                background-color: #ffffff;
                color: #2c3e50;
                border: 1px solid #e9ecef;
                border-radius: 6px;
                padding: 10px;
                selection-background-color: #3498db;
                selection-color: #ffffff;
            }
        """)
        
        layout.addWidget(self.content_browser)
        
        # Button bar
        button_layout = QHBoxLayout()
        
        # Save button
        self.save_button = QPushButton("Save Report")
        self.save_button.clicked.connect(self.save_report)
        
        # Export options
        self.export_combo = QComboBox()
        self.export_combo.addItems(["Markdown (.md)", "HTML (.html)", "Text (.txt)"])
        
        self.export_button = QPushButton("Export")
        self.export_button.clicked.connect(self.export_report)
        
        # Close button
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(QLabel("Export as:"))
        button_layout.addWidget(self.export_combo)
        button_layout.addWidget(self.export_button)
        button_layout.addStretch()
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
        # Status bar
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
    def render_markdown(self):
        """Render the markdown content to HTML."""
        try:
            self.status_label.setText("Rendering markdown...")
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
            
            # Render markdown to HTML
            html_content = MarkdownRenderer.render_markdown(self.markdown_content)
            
            # Set the HTML content
            self.content_browser.setHtml(html_content)
            
            self.status_label.setText(f"Report loaded successfully")
            self.progress_bar.setVisible(False)
            
        except Exception as e:
            self.status_label.setText(f"Error rendering markdown: {e}")
            self.progress_bar.setVisible(False)
    
    def search_text(self):
        """Search for text in the document."""
        search_term = self.search_input.text()
        if not search_term:
            return
        
        # Clear previous highlights
        cursor = self.content_browser.textCursor()
        cursor.clearSelection()
        
        # Find text
        case_sensitive = self.search_options.currentText() == "Case Sensitive"
        flags = QTextCursor.FindFlag(0)
        if case_sensitive:
            flags = QTextCursor.FindFlag.FindCaseSensitively
        
        found = self.content_browser.find(search_term, flags)
        
        if found:
            self.status_label.setText(f"Found '{search_term}'")
        else:
            self.status_label.setText(f"'{search_term}' not found")
    
    def find_next(self):
        """Find next occurrence of search term."""
        search_term = self.search_input.text()
        if search_term:
            case_sensitive = self.search_options.currentText() == "Case Sensitive"
            flags = QTextCursor.FindFlag(0)
            if case_sensitive:
                flags = QTextCursor.FindFlag.FindCaseSensitively
            
            found = self.content_browser.find(search_term, flags)
            if not found:
                # Wrap around to beginning
                cursor = self.content_browser.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.Start)
                self.content_browser.setTextCursor(cursor)
                self.content_browser.find(search_term, flags)
    
    def find_previous(self):
        """Find previous occurrence of search term."""
        search_term = self.search_input.text()
        if search_term:
            case_sensitive = self.search_options.currentText() == "Case Sensitive"
            flags = QTextCursor.FindFlag.FindBackward
            if case_sensitive:
                flags |= QTextCursor.FindFlag.FindCaseSensitively
            
            found = self.content_browser.find(search_term, flags)
            if not found:
                # Wrap around to end
                cursor = self.content_browser.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.End)
                self.content_browser.setTextCursor(cursor)
                self.content_browser.find(search_term, flags)
    
    def save_report(self):
        """Save the report as markdown."""
        from PyQt6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Report", "ai_code_review_report.md", 
            "Markdown Files (*.md);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.markdown_content)
                self.status_label.setText(f"Report saved to {file_path}")
            except Exception as e:
                self.status_label.setText(f"Error saving report: {e}")
    
    def export_report(self):
        """Export the report in different formats."""
        from PyQt6.QtWidgets import QFileDialog
        
        export_format = self.export_combo.currentText()
        
        if "HTML" in export_format:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export Report", "ai_code_review_report.html", 
                "HTML Files (*.html);;All Files (*)"
            )
            if file_path:
                try:
                    html_content = MarkdownRenderer.render_markdown(self.markdown_content)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    self.status_label.setText(f"Report exported to {file_path}")
                except Exception as e:
                    self.status_label.setText(f"Error exporting report: {e}")
        
        elif "Text" in export_format:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export Report", "ai_code_review_report.txt", 
                "Text Files (*.txt);;All Files (*)"
            )
            if file_path:
                try:
                    # Convert markdown to plain text
                    text_content = re.sub(r'#+\s*', '', self.markdown_content)  # Remove headers
                    text_content = re.sub(r'\*\*(.*?)\*\*', r'\1', text_content)  # Remove bold
                    text_content = re.sub(r'\*(.*?)\*', r'\1', text_content)  # Remove italic
                    text_content = re.sub(r'`(.*?)`', r'\1', text_content)  # Remove code
                    text_content = re.sub(r'```.*?\n(.*?)\n```', r'\1', text_content, flags=re.DOTALL)  # Remove code blocks
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(text_content)
                    self.status_label.setText(f"Report exported to {file_path}")
                except Exception as e:
                    self.status_label.setText(f"Error exporting report: {e}")
        
        else:  # Markdown
            self.save_report() 