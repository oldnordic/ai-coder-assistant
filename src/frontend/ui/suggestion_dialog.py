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
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, 
                             QPushButton, QDialogButtonBox, QWidget)
from PyQt6.QtGui import QFont
from backend.utils.constants import (
    DIALOG_DEFAULT_X, DIALOG_DEFAULT_Y, DIALOG_DEFAULT_WIDTH, DIALOG_DEFAULT_HEIGHT,
    CONTEXT_TEXT_MAX_HEIGHT, DEFAULT_BACKGROUND_COLOR, DEFAULT_FOREGROUND_COLOR, DEFAULT_BORDER_COLOR,
    PROGRESS_MAX, PROGRESS_MIN, PROGRESS_COMPLETE, DEFAULT_FONT_WEIGHT, DEFAULT_TEXT_COLOR
)

class SuggestionDialog(QDialog):
    def __init__(self, suggestion_data, explanation, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI Code Suggestion")
        self.setGeometry(DIALOG_DEFAULT_X, DIALOG_DEFAULT_Y, DIALOG_DEFAULT_WIDTH, DIALOG_DEFAULT_HEIGHT)

        # --- Custom Result Codes ---
        self.ApplyCode = 1
        self.CancelCode = 0
        self.CancelAllCode = 2

        # Ensure we have valid data
        if not suggestion_data:
            suggestion_data = {}
        if not explanation:
            explanation = "No explanation available"

        main_layout = QVBoxLayout(self)

        # --- Issue Information Header ---
        issue_info_layout = QHBoxLayout()
        
        # Issue type and severity
        issue_type = suggestion_data.get('issue_type', 'unknown')
        severity = suggestion_data.get('severity', 'medium')
        
        # Color coding for severity
        severity_colors = {
            'critical': '#FF4444',
            'high': '#FF8800', 
            'medium': '#FFCC00',
            'low': '#44FF44'
        }
        severity_color = severity_colors.get(severity, '#888888')
        
        issue_type_label = QLabel(f"<b>Type:</b> {issue_type.replace('_', ' ').title()}")
        severity_label = QLabel(f"<b>Severity:</b> <span style='color: {severity_color};'>{severity.upper()}</span>")
        
        issue_info_layout.addWidget(issue_type_label)
        issue_info_layout.addWidget(severity_label)
        issue_info_layout.addStretch()
        
        # File and line information
        file_path = suggestion_data.get('file_path', 'unknown')
        line_number = suggestion_data.get('line_number', 0)
        language = suggestion_data.get('language', 'unknown')
        
        file_info_label = QLabel(f"<b>File:</b> {file_path}:{line_number+1} ({language})")
        issue_info_layout.addWidget(file_info_label)
        
        main_layout.addLayout(issue_info_layout)

        # --- Issue Description ---
        description = suggestion_data.get('description', 'No description available')
        description_label = QLabel(f"<b>Issue Description:</b> {description}")
        description_label.setWordWrap(True)
        description_label.setStyleSheet("background-color: #2F2F2F; padding: 8px; border-radius: 4px;")
        main_layout.addWidget(description_label)

        # --- Code Context (if available) ---
        if 'context' in suggestion_data and suggestion_data['context']:
            context_label = QLabel("<b>Additional Context:</b>")
            context_text = QTextEdit()
            context_text.setReadOnly(True)
            context_text.setMaximumHeight(CONTEXT_TEXT_MAX_HEIGHT)
            context_text.setText(str(suggestion_data['context']))
            context_text.setStyleSheet(f"background-color: {DEFAULT_BACKGROUND_COLOR}; color: {DEFAULT_FOREGROUND_COLOR}; border: 1px solid {DEFAULT_BORDER_COLOR};")
            main_layout.addWidget(context_label)
            main_layout.addWidget(context_text)

        # --- Code Diff View ---
        diff_view = QWidget()
        diff_layout = QVBoxLayout(diff_view)
        
        original_label = QLabel("Original Code:")
        self.original_code_text = QTextEdit()
        self.original_code_text.setReadOnly(True)
        self.original_code_text.setText(suggestion_data.get('code_snippet', 'No code snippet available'))
        self.original_code_text.setStyleSheet("background-color: #5C3333; color: #F0F0F0; border: 1px solid #7a4b4b;")

        proposed_label = QLabel("AI Suggested Improvement:")
        self.proposed_code_text = QTextEdit()
        self.proposed_code_text.setReadOnly(True)
        self.proposed_code_text.setText(suggestion_data.get('suggested_improvement', 'No suggestion available'))
        self.proposed_code_text.setStyleSheet("background-color: #335C33; color: #F0F0F0; border: 1px solid #4b7a4b;")

        mono_font = QFont("monospace")
        mono_font.setStyleHint(QFont.StyleHint.TypeWriter)
        self.original_code_text.setFont(mono_font)
        self.proposed_code_text.setFont(mono_font)

        diff_layout.addWidget(original_label)
        diff_layout.addWidget(self.original_code_text)
        diff_layout.addWidget(proposed_label)
        diff_layout.addWidget(self.proposed_code_text)
        main_layout.addWidget(diff_view)
        
        # --- AI Explanation ---
        explanation_label = QLabel("AI Analysis & Explanation:")
        self.explanation_text = QTextEdit()
        self.explanation_text.setReadOnly(True)
        self.explanation_text.setText(explanation)
        self.explanation_text.setStyleSheet("background-color: #2F3C5F; color: #F0F0F0; border: 1px solid #4B617A;")
        main_layout.addWidget(explanation_label)
        main_layout.addWidget(self.explanation_text)

        # --- User Feedback ---
        user_justification_label = QLabel("Your Feedback (for AI learning):")
        self.user_justification_text = QTextEdit()
        self.user_justification_text.setPlaceholderText("If you disagree with the suggestion, provide your own corrected code or explain why here...")
        self.user_justification_text.setStyleSheet("background-color: #2F3C5F; color: #F0F0F0; border: 1px solid #4B617A;")
        main_layout.addWidget(user_justification_label)
        main_layout.addWidget(self.user_justification_text)

        # --- Buttons ---
        # Use a standard button box for Apply and Cancel
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Apply | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.apply_clicked)
        self.button_box.rejected.connect(self.reject) # Standard reject just closes with code 0

        # --- FIXED: Create a separate button for "Cancel All" ---
        self.cancel_all_button = QPushButton("Cancel All Reviews")
        self.cancel_all_button.clicked.connect(self.cancel_all_clicked)

        # Add both to a horizontal layout
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.cancel_all_button)
        button_layout.addStretch()
        button_layout.addWidget(self.button_box)
        main_layout.addLayout(button_layout)

    def apply_clicked(self):
        """Close the dialog and return the custom 'Apply' code."""
        self.done(self.ApplyCode)

    def cancel_all_clicked(self):
        """Close the dialog and return the custom 'CancelAll' code."""
        self.done(self.CancelAllCode)

    def get_user_justification(self):
        """Returns the text from the user justification box."""
        return self.user_justification_text.toPlainText().strip()