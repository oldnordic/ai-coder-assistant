"""
Security Intelligence Tab

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

"""
Security Intelligence Tab - Track security breaches, CVEs, and patches.
"""

import logging
from typing import List, Dict, Any
from datetime import datetime

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QComboBox,
    QSpinBox,
    QProgressBar,
    QGroupBox,
    QHeaderView,
    QMessageBox,
    QCheckBox,
    QLineEdit,
)

from src.frontend.controllers.backend_controller import BackendController

logger = logging.getLogger(__name__)


class SecurityIntelligenceTab(QWidget):
    """Security Intelligence Tab Widget."""

    def __init__(self, backend_controller: BackendController):
        super().__init__()
        self.backend_controller = backend_controller
        self.setup_ui()
        self.load_sample_data()

    def setup_ui(self):
        """Setup the user interface."""
        main_layout = QVBoxLayout()

        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Security Intelligence")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        # Refresh button
        self.refresh_button = QPushButton("Refresh Data")
        self.refresh_button.clicked.connect(self.refresh_data)
        header_layout.addWidget(self.refresh_button)
        
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # Create tab widget for different security data types
        self.tab_widget = QTabWidget()
        
        # Vulnerabilities Tab
        self.vulnerabilities_tab = self.create_vulnerabilities_tab()
        self.tab_widget.addTab(self.vulnerabilities_tab, "Vulnerabilities")
        
        # Security Breaches Tab
        self.breaches_tab = self.create_breaches_tab()
        self.tab_widget.addTab(self.breaches_tab, "Security Breaches")
        
        # Analysis Tab
        self.analysis_tab = self.create_analysis_tab()
        self.tab_widget.addTab(self.analysis_tab, "Security Analysis")
        
        main_layout.addWidget(self.tab_widget)
        
        # Status bar
        self.status_label = QLabel("Ready")
        main_layout.addWidget(self.status_label)
        
        self.setLayout(main_layout)

    def create_vulnerabilities_tab(self) -> QWidget:
        """Create the vulnerabilities tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Controls
        controls_layout = QHBoxLayout()
        
        controls_layout.addWidget(QLabel("Severity Filter:"))
        self.severity_filter = QComboBox()
        self.severity_filter.addItems(["All", "Critical", "High", "Medium", "Low"])
        self.severity_filter.currentTextChanged.connect(self.filter_vulnerabilities)
        controls_layout.addWidget(self.severity_filter)
        
        controls_layout.addStretch()
        
        self.load_vuln_button = QPushButton("Load Vulnerabilities")
        self.load_vuln_button.clicked.connect(self.load_vulnerabilities)
        controls_layout.addWidget(self.load_vuln_button)
        
        layout.addLayout(controls_layout)
        
        # Vulnerabilities table
        self.vulnerabilities_table = QTableWidget()
        self.vulnerabilities_table.setColumnCount(5)
        self.vulnerabilities_table.setHorizontalHeaderLabels([
            "CVE ID", "Title", "Severity", "Published", "Status"
        ])
        
        # Set column widths
        header = self.vulnerabilities_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.vulnerabilities_table)
        
        # Details panel
        self.vuln_details = QTextEdit()
        self.vuln_details.setMaximumHeight(150)
        self.vuln_details.setReadOnly(True)
        layout.addWidget(self.vuln_details)
        
        # Connect table selection
        self.vulnerabilities_table.itemSelectionChanged.connect(self.on_vulnerability_selected)
        
        tab.setLayout(layout)
        return tab

    def create_breaches_tab(self) -> QWidget:
        """Create the security breaches tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Controls
        controls_layout = QHBoxLayout()
        
        controls_layout.addStretch()
        
        self.load_breach_button = QPushButton("Load Breaches")
        self.load_breach_button.clicked.connect(self.load_breaches)
        controls_layout.addWidget(self.load_breach_button)
        
        layout.addLayout(controls_layout)
        
        # Breaches table
        self.breaches_table = QTableWidget()
        self.breaches_table.setColumnCount(5)
        self.breaches_table.setHorizontalHeaderLabels([
            "Company", "Date", "Records Affected", "Type", "Details"
        ])
        
        # Set column widths
        header = self.breaches_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.breaches_table)
        
        tab.setLayout(layout)
        return tab

    def create_analysis_tab(self) -> QWidget:
        """Create the security analysis tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Analysis controls
        controls_group = QGroupBox("Security Analysis")
        controls_layout = QVBoxLayout()
        
        # Target path
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Target Path:"))
        self.target_path_input = QLineEdit()
        self.target_path_input.setPlaceholderText("Enter path to analyze")
        path_layout.addWidget(self.target_path_input)
        controls_layout.addLayout(path_layout)
        
        # Analysis type
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Analysis Type:"))
        self.analysis_type_combo = QComboBox()
        self.analysis_type_combo.addItems([
            "Code Security Scan",
            "Dependency Vulnerability Scan",
            "Secrets Detection"
        ])
        type_layout.addWidget(self.analysis_type_combo)
        controls_layout.addLayout(type_layout)
        
        # Start button
        self.start_analysis_button = QPushButton("Start Analysis")
        self.start_analysis_button.clicked.connect(self.start_analysis)
        controls_layout.addWidget(self.start_analysis_button)
        
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
        
        # Progress
        self.analysis_progress = QProgressBar()
        self.analysis_progress.setVisible(False)
        layout.addWidget(self.analysis_progress)
        
        # Results
        results_group = QGroupBox("Analysis Results")
        results_layout = QVBoxLayout()
        
        self.analysis_results = QTextEdit()
        self.analysis_results.setReadOnly(True)
        results_layout.addWidget(self.analysis_results)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab

    def load_sample_data(self):
        """Load sample data for demonstration."""
        self.load_vulnerabilities()
        self.load_breaches()

    def load_vulnerabilities(self):
        """Load vulnerabilities data."""
        try:
            # Sample vulnerability data
            vulnerabilities = [
                {
                    "id": "CVE-2024-1234",
                    "title": "SQL Injection in User Authentication",
                    "severity": "High",
                    "published_date": "2024-01-15",
                    "status": "Open"
                },
                {
                    "id": "CVE-2024-1235",
                    "title": "Cross-Site Scripting in Search Function",
                    "severity": "Medium",
                    "published_date": "2024-01-10",
                    "status": "Open"
                },
                {
                    "id": "CVE-2024-1236",
                    "title": "Buffer Overflow in File Upload",
                    "severity": "Critical",
                    "published_date": "2024-01-05",
                    "status": "Patched"
                }
            ]
            
            self.populate_vulnerabilities_table(vulnerabilities)
            self.status_label.setText(f"Loaded {len(vulnerabilities)} vulnerabilities")
            
        except Exception as e:
            logger.error(f"Error loading vulnerabilities: {e}")
            self.status_label.setText("Error loading vulnerabilities")

    def load_breaches(self):
        """Load security breaches data."""
        try:
            # Sample breach data
            breaches = [
                {
                    "company": "TechCorp Inc",
                    "date": "2024-01-20",
                    "records_affected": "2.3M",
                    "type": "Data Breach",
                    "description": "Unauthorized access to customer database"
                },
                {
                    "company": "SecureBank",
                    "date": "2024-01-18",
                    "records_affected": "500K",
                    "type": "Ransomware",
                    "description": "Ransomware attack affecting customer accounts"
                }
            ]
            
            self.populate_breaches_table(breaches)
            self.status_label.setText(f"Loaded {len(breaches)} security breaches")
            
        except Exception as e:
            logger.error(f"Error loading breaches: {e}")
            self.status_label.setText("Error loading breaches")

    def populate_vulnerabilities_table(self, vulnerabilities: List[Dict[str, Any]]):
        """Populate the vulnerabilities table with data."""
        self.vulnerabilities_table.setRowCount(len(vulnerabilities))
        
        for row, vuln in enumerate(vulnerabilities):
            # CVE ID
            cve_id = vuln.get("id", "N/A")
            self.vulnerabilities_table.setItem(row, 0, QTableWidgetItem(cve_id))
            
            # Title
            title = vuln.get("title", "N/A")
            self.vulnerabilities_table.setItem(row, 1, QTableWidgetItem(title))
            
            # Severity
            severity = vuln.get("severity", "Unknown")
            severity_item = QTableWidgetItem(severity)
            self.set_severity_color(severity_item, severity)
            self.vulnerabilities_table.setItem(row, 2, severity_item)
            
            # Published date
            published = vuln.get("published_date", "N/A")
            self.vulnerabilities_table.setItem(row, 3, QTableWidgetItem(str(published)))
            
            # Status
            status = vuln.get("status", "Open")
            self.vulnerabilities_table.setItem(row, 4, QTableWidgetItem(status))

    def populate_breaches_table(self, breaches: List[Dict[str, Any]]):
        """Populate the breaches table with data."""
        self.breaches_table.setRowCount(len(breaches))
        
        for row, breach in enumerate(breaches):
            # Company
            company = breach.get("company", "N/A")
            self.breaches_table.setItem(row, 0, QTableWidgetItem(company))
            
            # Date
            date = breach.get("date", "N/A")
            self.breaches_table.setItem(row, 1, QTableWidgetItem(str(date)))
            
            # Records affected
            records = breach.get("records_affected", "N/A")
            self.breaches_table.setItem(row, 2, QTableWidgetItem(str(records)))
            
            # Type
            breach_type = breach.get("type", "N/A")
            self.breaches_table.setItem(row, 3, QTableWidgetItem(breach_type))
            
            # Details
            details = breach.get("description", "N/A")
            self.breaches_table.setItem(row, 4, QTableWidgetItem(details))

    def set_severity_color(self, item: QTableWidgetItem, severity: str):
        """Set color for severity levels."""
        if severity.lower() == "critical":
            item.setBackground(QColor(255, 0, 0, 100))  # Red
        elif severity.lower() == "high":
            item.setBackground(QColor(255, 165, 0, 100))  # Orange
        elif severity.lower() == "medium":
            item.setBackground(QColor(255, 255, 0, 100))  # Yellow
        elif severity.lower() == "low":
            item.setBackground(QColor(0, 255, 0, 100))  # Green

    def filter_vulnerabilities(self):
        """Filter vulnerabilities by severity."""
        severity_filter = self.severity_filter.currentText()
        
        for row in range(self.vulnerabilities_table.rowCount()):
            severity_item = self.vulnerabilities_table.item(row, 2)
            if severity_item:
                severity = severity_item.text()
                if severity_filter == "All" or severity == severity_filter:
                    self.vulnerabilities_table.setRowHidden(row, False)
                else:
                    self.vulnerabilities_table.setRowHidden(row, True)

    def on_vulnerability_selected(self):
        """Handle vulnerability selection."""
        current_row = self.vulnerabilities_table.currentRow()
        if current_row >= 0:
            # Get vulnerability details and display them
            cve_id = self.vulnerabilities_table.item(current_row, 0).text()
            title = self.vulnerabilities_table.item(current_row, 1).text()
            severity = self.vulnerabilities_table.item(current_row, 2).text()
            
            details = f"CVE ID: {cve_id}\n"
            details += f"Title: {title}\n"
            details += f"Severity: {severity}\n"
            details += f"Status: {self.vulnerabilities_table.item(current_row, 4).text()}\n\n"
            details += "Additional details would be loaded from the backend..."
            
            self.vuln_details.setPlainText(details)

    def refresh_data(self):
        """Refresh all security data."""
        self.load_vulnerabilities()
        self.load_breaches()
        self.status_label.setText("Data refreshed")

    def start_analysis(self):
        """Start security analysis."""
        target_path = self.target_path_input.text().strip()
        analysis_type = self.analysis_type_combo.currentText()
        
        if not target_path:
            QMessageBox.warning(self, "Input Required", "Please enter a target path for analysis.")
            return
        
        self.start_analysis_button.setEnabled(False)
        self.analysis_progress.setVisible(True)
        self.analysis_progress.setValue(0)
        self.analysis_results.clear()
        
        # Simulate analysis
        self.analysis_progress.setValue(25)
        QTimer.singleShot(1000, lambda: self.analysis_progress.setValue(50))
        QTimer.singleShot(2000, lambda: self.analysis_progress.setValue(75))
        QTimer.singleShot(3000, lambda: self.complete_analysis())

    def complete_analysis(self):
        """Complete the security analysis."""
        self.analysis_progress.setValue(100)
        self.start_analysis_button.setEnabled(True)
        self.analysis_progress.setVisible(False)
        
        # Display results
        results = "Security Analysis Results:\n\n"
        results += "Vulnerabilities Found: 2\n"
        results += "Security Score: 75/100\n\n"
        results += "Recommendations:\n"
        results += "• Use parameterized queries to prevent SQL injection\n"
        results += "• Sanitize user input to prevent XSS attacks\n"
        results += "• Implement proper authentication and authorization\n"
        
        self.analysis_results.setPlainText(results)
        self.status_label.setText("Analysis completed") 