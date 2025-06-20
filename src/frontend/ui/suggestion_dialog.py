"""
suggestion_dialog.py

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

# suggestion_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QGroupBox
)
from PyQt6.QtCore import Qt
from typing import Dict, Any, Optional
from backend.utils.constants import (
    DIALOG_DEFAULT_X, DIALOG_DEFAULT_Y, DIALOG_DEFAULT_WIDTH, DIALOG_DEFAULT_HEIGHT,
    CONTEXT_TEXT_MAX_HEIGHT, DEFAULT_BACKGROUND_COLOR, DEFAULT_FOREGROUND_COLOR, DEFAULT_BORDER_COLOR,
    PROGRESS_MAX, PROGRESS_MIN, PROGRESS_COMPLETE, DEFAULT_FONT_WEIGHT, DEFAULT_TEXT_COLOR
)

class SuggestionDialog(QDialog):
    """Dialog for reviewing code suggestions interactively."""
    
    ApplyCode = QDialog.DialogCode.Accepted
    CancelCode = QDialog.DialogCode.Rejected
    CancelAllCode = 2
    
    def __init__(self, suggestion: Dict[str, Any], ai_explanation: str, parent: Optional[QDialog] = None):
        super().__init__(parent)
        self.suggestion = suggestion
        self.ai_explanation = ai_explanation
        self.user_justification = ""
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Review Code Suggestion")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        
        layout = QVBoxLayout(self)
        
        # File and line info
        file_info = QLabel(f"<b>File:</b> {self.suggestion.get('file_path', 'N/A')}")
        line_info = QLabel(f"<b>Line:</b> {self.suggestion.get('line_number', 'N/A')}")
        layout.addWidget(file_info)
        layout.addWidget(line_info)
        
        # Issue description
        description_group = QGroupBox("Issue Description")
        description_layout = QVBoxLayout(description_group)
        description = QLabel(self.suggestion.get('description', 'No description available'))
        description.setWordWrap(True)
        description_layout.addWidget(description)
        layout.addWidget(description_group)
        
        # Original code
        if self.suggestion.get('code_snippet'):
            original_group = QGroupBox("Original Code")
            original_layout = QVBoxLayout(original_group)
            original_code = QTextEdit()
            original_code.setPlainText(self.suggestion['code_snippet'])
            original_code.setReadOnly(True)
            original_layout.addWidget(original_code)
            layout.addWidget(original_group)
        
        # Suggested improvement
        if self.suggestion.get('suggested_improvement'):
            suggested_group = QGroupBox("Suggested Improvement")
            suggested_layout = QVBoxLayout(suggested_group)
            suggested_code = QTextEdit()
            suggested_code.setPlainText(self.suggestion['suggested_improvement'])
            suggested_code.setReadOnly(True)
            suggested_layout.addWidget(suggested_code)
            layout.addWidget(suggested_group)
        
        # AI explanation
        ai_group = QGroupBox("AI Explanation")
        ai_layout = QVBoxLayout(ai_group)
        ai_text = QTextEdit()
        ai_text.setPlainText(self.ai_explanation)
        ai_text.setReadOnly(True)
        ai_layout.addWidget(ai_text)
        layout.addWidget(ai_group)
        
        # User feedback
        feedback_group = QGroupBox("Your Feedback (Optional)")
        feedback_layout = QVBoxLayout(feedback_group)
        self.feedback_text = QTextEdit()
        self.feedback_text.setPlaceholderText("Enter your feedback or justification here...")
        feedback_layout.addWidget(self.feedback_text)
        layout.addWidget(feedback_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        apply_button = QPushButton("Apply Suggestion")
        apply_button.clicked.connect(self.accept)
        
        skip_button = QPushButton("Skip")
        skip_button.clicked.connect(self.reject)
        
        cancel_all_button = QPushButton("Cancel Review")
        cancel_all_button.clicked.connect(self.cancel_all)
        
        button_layout.addWidget(apply_button)
        button_layout.addWidget(skip_button)
        button_layout.addWidget(cancel_all_button)
        layout.addLayout(button_layout)
    
    def get_user_justification(self) -> str:
        """Get the user's feedback or justification."""
        return self.feedback_text.toPlainText().strip()
    
    def cancel_all(self):
        """Cancel the entire review process."""
        self.done(self.CancelAllCode)