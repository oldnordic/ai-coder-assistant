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

from typing import Optional, List, Dict, Any, cast
import re
import os
import markdown
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextBrowser, QLabel, QLineEdit, QComboBox,
    QDialogButtonBox, QProgressBar, QSplitter,
    QFileDialog, QMessageBox, QMenu
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject, QMarginsF, QUrl
from PyQt6.QtGui import (
    QFont, QTextCursor, QTextCharFormat, QColor,
    QPageSize, QPageLayout, QTextDocument,
    QAction, QPainter, QAbstractTextDocumentLayout
)
from PyQt6.QtPrintSupport import QPrinter, QPageSetupDialog
from backend.utils.constants import (
    WINDOW_DEFAULT_X, WINDOW_DEFAULT_Y, WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT,
    DIALOG_DEFAULT_WIDTH, DIALOG_DEFAULT_HEIGHT, 
    LOG_CONSOLE_MAX_HEIGHT, DEFAULT_BACKGROUND_COLOR, DEFAULT_FOREGROUND_COLOR, DEFAULT_BORDER_COLOR,
    MARKDOWN_VIEWER_WIDTH, MARKDOWN_VIEWER_HEIGHT, MARKDOWN_VIEWER_FONT_SIZE,
    MARKDOWN_VIEWER_FONT_FAMILY, MARKDOWN_VIEWER_BG_COLOR, MARKDOWN_VIEWER_FG_COLOR
)
from backend.utils.constants import DEFAULT_FONT_WEIGHT, DEFAULT_TEXT_COLOR

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
                    background-color: #2F2F2F; 
                    color: #CCCCCC;
                    font-size: 14px;
                }}
                h1 {{ 
                    color: #CCCCCC; 
                    border-bottom: 3px solid #007bff; 
                    padding-bottom: 10px; 
                    font-size: 28px;
                    margin-top: 30px;
                    margin-bottom: 20px;
                }}
                h2 {{ 
                    color: #CCCCCC; 
                    border-bottom: 2px solid #444444; 
                    padding-bottom: 8px; 
                    font-size: 24px;
                    margin-top: 25px;
                    margin-bottom: 15px;
                }}
                h3 {{ 
                    color: #CCCCCC; 
                    font-size: 20px;
                    margin-top: 20px;
                    margin-bottom: 10px;
                }}
                p {{
                    margin-bottom: 15px;
                    color: #CCCCCC;
                }}
                code {{ 
                    background-color: #1F1F1F; 
                    color: #FF6B6B;
                    padding: 3px 6px; 
                    border-radius: 4px; 
                    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                    font-size: 13px;
                    border: 1px solid #444444;
                }}
                pre {{ 
                    background-color: #1F1F1F; 
                    color: #CCCCCC; 
                    padding: 20px; 
                    border-radius: 8px; 
                    overflow-x: auto;
                    border: 1px solid #444444;
                    margin: 15px 0;
                }}
                pre code {{ 
                    background-color: transparent; 
                    padding: 0; 
                    color: #CCCCCC;
                    border: none;
                }}
                ul {{ 
                    padding-left: 25px; 
                    margin-bottom: 15px;
                }}
                li {{ 
                    margin-bottom: 8px; 
                    color: #CCCCCC;
                }}
                a {{ 
                    color: #4ECDC4; 
                    text-decoration: none; 
                    font-weight: {DEFAULT_FONT_WEIGHT};
                }}
                a:hover {{ 
                    text-decoration: underline; 
                    color: #007bff;
                }}
                .issue-section {{ 
                    background-color: #1F1F1F; 
                    padding: 20px; 
                    margin: 15px 0; 
                    border-radius: 8px; 
                    border-left: 5px solid #007bff;
                    border: 1px solid #444444;
                }}
                .critical {{ 
                    border-left-color: #FF6B6B; 
                    background-color: #2F1F1F;
                }}
                .high {{ 
                    border-left-color: #FFA500; 
                    background-color: #2F2F1F;
                }}
                .medium {{ 
                    border-left-color: #FFD700; 
                    background-color: #2F2F1F;
                }}
                .low {{ 
                    border-left-color: #4ECDC4; 
                    background-color: #1F2F1F;
                }}
                .summary {{
                    background-color: #1F1F2F;
                    padding: 15px;
                    border-radius: 6px;
                    border: 1px solid #444444;
                    margin: 15px 0;
                }}
                .recommendation {{
                    background-color: #2F2F1F;
                    padding: 15px;
                    border-radius: 6px;
                    border: 1px solid #444444;
                    margin: 15px 0;
                }}
                .file-path {{
                    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                    background-color: #1F1F1F;
                    padding: 4px 8px;
                    border-radius: 4px;
                    color: #CCCCCC;
                    font-size: 12px;
                }}
                .severity-high {{
                    color: #FF6B6B;
                    font-weight: bold;
                }}
                .severity-medium {{
                    color: #FFA500;
                    font-weight: bold;
                }}
                .severity-low {{
                    color: #4ECDC4;
                    font-weight: bold;
                }}
                .severity-critical {{
                    color: #FF4757;
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
    """Dialog for viewing and exporting markdown content."""
    
    def __init__(self, markdown_content: str, parent: Optional[QDialog] = None) -> None:
        """Initialize the dialog with markdown content.
        
        Args:
            markdown_content (str): The markdown content to display
            parent (Optional[QDialog]): Parent widget
        """
        super().__init__(parent)
        self.markdown_content = markdown_content
        self.text_browser = QTextBrowser(self)  # Initialize text browser
        self.search_input = QLineEdit(self)  # Initialize search input
        self.search_options = QComboBox(self)  # Initialize search options
        self.setup_ui()
        self.display_markdown()

    def display_markdown(self):
        """Convert markdown to HTML and display it."""
        try:
            # Convert markdown to HTML
            html_content = markdown.markdown(
                self.markdown_content,
                extensions=['fenced_code', 'tables', 'nl2br']
            )
            
            # Set the HTML content
            self.text_browser.setHtml(html_content)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to render markdown: {str(e)}"
            )

    def setup_ui(self) -> None:
        """Set up the dialog UI."""
        self.setWindowTitle("Report Viewer")
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        # Save menu
        save_menu = QMenu(self)
        save_menu.addAction("Save as Markdown", self.save_as_markdown)
        save_menu.addAction("Save as HTML", self.save_as_html)
        save_menu.addAction("Save as TXT", self.save_as_txt)
        save_menu.addAction("Save as PDF", self.save_as_pdf)
        
        save_button = QPushButton("Save As...")
        save_button.setMenu(save_menu)
        toolbar.addWidget(save_button)
        
        # Search controls
        self.search_label = QLabel("Search:", self)
        toolbar.addWidget(self.search_label)
        
        toolbar.addWidget(self.search_input)
        self.search_input.textChanged.connect(self.highlight_search)
        
        self.search_options.addItems(["Case Sensitive", "Case Insensitive"])
        toolbar.addWidget(self.search_options)
        
        layout.addLayout(toolbar)
        
        # Text browser
        layout.addWidget(self.text_browser)
        self.text_browser.anchorClicked.connect(self.handle_link_click)

    def save_as_txt(self):
        """Save the content as plain text file."""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save as Text", "", "Text Files (*.txt)"
            )
            
            if file_path:
                if not file_path.endswith('.txt'):
                    file_path += '.txt'
                
                # Convert HTML to plain text while preserving structure
                text_content = self.text_browser.toPlainText()
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(text_content)
                
                QMessageBox.information(
                    self, "Success", f"Report saved as text to {file_path}"
                )
        
        except Exception as e:
            QMessageBox.warning(
                self, "Error", f"Failed to save text file: {str(e)}"
            )

    def save_as_pdf(self):
        """Save the content as PDF file."""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save as PDF", "", "PDF Files (*.pdf)"
            )
            
            if file_path:
                if not file_path.endswith('.pdf'):
                    file_path += '.pdf'
                
                # Create printer with high resolution
                printer = QPrinter(QPrinter.PrinterMode.HighResolution)
                printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
                printer.setOutputFileName(file_path)
                
                # Set paper size to A4 and margins
                printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
                printer.setPageMargins(QMarginsF(20, 20, 20, 20), QPageLayout.Unit.Millimeter)
                
                # Create a document from the text browser's content
                doc = QTextDocument()
                doc.setHtml(self.text_browser.toHtml())
                
                # Set the page size to match the printer (using DevicePixel unit)
                doc.setPageSize(printer.pageRect(QPrinter.Unit.DevicePixel).size())
                
                # Print the document to PDF
                doc.print(printer)
                
                QMessageBox.information(
                    self, "Success", f"Report saved as PDF to {file_path}"
                )
        
        except Exception as e:
            QMessageBox.warning(
                self, "Error", f"Failed to save PDF file: {str(e)}"
            )

    def save_as_html(self):
        """Save the content as HTML file."""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save as HTML", "", "HTML Files (*.html)"
            )
            
            if file_path:
                if not file_path.endswith('.html'):
                    file_path += '.html'
                
                html_content = self.text_browser.toHtml()
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                QMessageBox.information(
                    self, "Success", f"Report saved as HTML to {file_path}"
                )
        
        except Exception as e:
            QMessageBox.warning(
                self, "Error", f"Failed to save HTML file: {str(e)}"
            )
    
    def save_as_markdown(self):
        """Save the original markdown content."""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save as Markdown", "", "Markdown Files (*.md)"
            )
            
            if file_path:
                if not file_path.endswith('.md'):
                    file_path += '.md'
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.markdown_content)
                
                QMessageBox.information(
                    self, "Success", f"Report saved as Markdown to {file_path}"
                )
        
        except Exception as e:
            QMessageBox.warning(
                self, "Error", f"Failed to save Markdown file: {str(e)}"
            )

    def highlight_search(self):
        """Highlight all occurrences of the search text."""
        search_text = self.search_input.text()
        if not search_text:
            # Clear any existing highlighting
            cursor = self.text_browser.textCursor()
            cursor.select(QTextCursor.SelectionType.Document)
            format = QTextCharFormat()
            cursor.setCharFormat(format)
            return

        # Create format for highlighting
        highlight_format = QTextCharFormat()
        highlight_format.setBackground(QColor(255, 255, 0, 100))  # Light yellow

        # Get the document
        document = self.text_browser.document()

        # Clear previous highlighting
        cursor = QTextCursor(document)
        cursor.select(QTextCursor.SelectionType.Document)
        format = QTextCharFormat()
        cursor.setCharFormat(format)

        # Find and highlight all occurrences
        cursor = QTextCursor(document)
        pattern = search_text
        if self.search_options.currentText() == "Case Insensitive":
            pattern = pattern.lower()
            while not cursor.isNull() and not cursor.atEnd():
                cursor = document.find(pattern, cursor, QTextDocument.FindFlag.FindCaseSensitively)
                if not cursor.isNull():
                    cursor.mergeCharFormat(highlight_format)
        else:
            while not cursor.isNull() and not cursor.atEnd():
                cursor = document.find(pattern, cursor)
                if not cursor.isNull():
                    cursor.mergeCharFormat(highlight_format)

    def find_next(self):
        """Find the next occurrence of the search text."""
        search_text = self.search_input.text()
        if not search_text:
            return

        flags = QTextDocument.FindFlag(0)
        if self.search_options.currentText() == "Case Sensitive":
            flags |= QTextDocument.FindFlag.FindCaseSensitively

        # Start from current cursor position
        cursor = self.text_browser.textCursor()
        
        # Find next occurrence
        found = self.text_browser.find(search_text, flags)
        
        if not found:
            # If not found from current position, try from start
            cursor = self.text_browser.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            self.text_browser.setTextCursor(cursor)
            found = self.text_browser.find(search_text, flags)
            
            if not found:
                QMessageBox.information(self, "Search", "No more occurrences found.")

    def find_previous(self):
        """Find the previous occurrence of the search text."""
        search_text = self.search_input.text()
        if not search_text:
            return

        flags = QTextDocument.FindFlag.FindBackward
        if self.search_options.currentText() == "Case Sensitive":
            flags |= QTextDocument.FindFlag.FindCaseSensitively

        # Start from current cursor position
        cursor = self.text_browser.textCursor()
        
        # Find previous occurrence
        found = self.text_browser.find(search_text, flags)
        
        if not found:
            # If not found from current position, try from end
            cursor = self.text_browser.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.text_browser.setTextCursor(cursor)
            found = self.text_browser.find(search_text, flags)
            
            if not found:
                QMessageBox.information(self, "Search", "No more occurrences found.")

    def handle_link_click(self, url: QUrl):
        """Handle link click event."""
        # Implement link handling logic here
        print(f"Link clicked: {url.toString()}") 