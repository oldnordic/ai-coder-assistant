from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QProgressBar, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

class LearningStatsPanel(QWidget):
    fineTuneRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.stats = {}
        self.finetune_status = {}

        self.layout = QVBoxLayout(self)
        self.examples_label = QLabel("Learning Examples: 0")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.finetune_label = QLabel("")
        self.finetune_button = QPushButton("Fine-tune Now!")
        self.finetune_button.setEnabled(False)
        self.finetune_button.clicked.connect(self.on_finetune_clicked)

        self.layout.addWidget(self.examples_label)
        self.layout.addWidget(self.progress_bar)
        self.layout.addWidget(self.finetune_label)
        self.layout.addWidget(self.finetune_button)
        self.setLayout(self.layout)

    def update_stats(self, stats: dict, finetune_status: dict):
        total = finetune_status.get("total_examples", 0)
        min_required = finetune_status.get("min_required", 100)
        ready = finetune_status.get("ready", False)
        percent = min(100, int(100 * total / max(1, min_required)))

        self.examples_label.setText(f"Learning Examples: {total} / {min_required}")
        self.progress_bar.setValue(percent)
        if ready:
            self.finetune_label.setText("Ready for fine-tuning!")
            self.finetune_button.setEnabled(True)
        else:
            self.finetune_label.setText("Collecting more examples for fine-tuning...")
            self.finetune_button.setEnabled(False)

    def on_finetune_clicked(self):
        reply = QMessageBox.question(
            self, "Confirm Fine-tune",
            "Are you sure you want to start model fine-tuning now?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.fineTuneRequested.emit() 