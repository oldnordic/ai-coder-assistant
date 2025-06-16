# suggestion_dialog.py
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, 
                             QPushButton, QDialogButtonBox, QWidget)
from PyQt6.QtGui import QFont

class SuggestionDialog(QDialog):
    def __init__(self, suggestion_data, explanation, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI Code Suggestion")
        self.setGeometry(150, 150, 800, 700)

        # --- Custom Result Codes ---
        self.ApplyCode = 1
        self.CancelCode = 0
        self.CancelAllCode = 2

        main_layout = QVBoxLayout(self)

        description_label = QLabel(f"<b>Issue:</b> {suggestion_data['description']}")
        description_label.setWordWrap(True)
        main_layout.addWidget(description_label)

        diff_view = QWidget()
        diff_layout = QVBoxLayout(diff_view)
        
        original_label = QLabel("Original Code:")
        self.original_code_text = QTextEdit()
        self.original_code_text.setReadOnly(True)
        self.original_code_text.setText(suggestion_data['original_code'])
        self.original_code_text.setStyleSheet("background-color: #5C3333; color: #F0F0F0; border: 1px solid #7a4b4b;")

        proposed_label = QLabel("Proposed Change:")
        self.proposed_code_text = QTextEdit()
        self.proposed_code_text.setReadOnly(True)
        self.proposed_code_text.setText(suggestion_data['proposed_code'])
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
        
        explanation_label = QLabel("AI Explanation (Based on Knowledge Base):")
        self.explanation_text = QTextEdit()
        self.explanation_text.setReadOnly(True)
        self.explanation_text.setText(explanation)
        main_layout.addWidget(explanation_label)
        main_layout.addWidget(self.explanation_text)

        user_justification_label = QLabel("Your Alternative or Justification (for AI learning):")
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