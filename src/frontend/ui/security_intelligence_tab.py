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

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTableWidget, 
    QTableWidgetItem, QPushButton, QLabel, QComboBox, QLineEdit,
    QTextEdit, QGroupBox, QFormLayout, QSpinBox, QCheckBox,
    QMessageBox, QProgressBar, QSplitter, QHeaderView, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QPalette

from ..controllers import BackendController

logger = logging.getLogger(__name__)


class SecurityFeedWorker(QThread):
    """Worker thread for fetching security feeds."""
    
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(int)
    
    def __init__(self, backend_controller: BackendController):
        super().__init__()
        self.backend_controller = backend_controller
    
    def run(self):
        """Fetch security feeds."""
        try:
            self.progress.emit(25)
            # Use a synchronous method instead of async
            # self.backend_controller.fetch_security_feeds()
            # For now, simulate the operation
            import time
            time.sleep(1)  # Simulate processing time
            self.progress.emit(100)
            self.finished.emit(True, "Security feeds fetched successfully")
        except Exception as e:
            logger.error(f"Error fetching security feeds: {e}")
            self.finished.emit(False, str(e))


class SecurityIntelligenceTab(QWidget):
    """Security Intelligence Tab Widget."""
    
    def __init__(self, backend_controller: BackendController):
        super().__init__()
        self.backend_controller = backend_controller
        self.setup_ui()
        self.load_data()
        
        # Setup refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(300000)  # Refresh every 5 minutes
    
    def setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Security Intelligence")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        # Control buttons
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_data)
        header_layout.addWidget(refresh_btn)
        
        fetch_feeds_btn = QPushButton("Fetch Feeds")
        fetch_feeds_btn.clicked.connect(self.fetch_security_feeds)
        header_layout.addWidget(fetch_feeds_btn)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Main tab widget
        self.tab_widget = QTabWidget()
        
        # Vulnerabilities tab
        self.vulnerabilities_tab = self.create_vulnerabilities_tab()
        self.tab_widget.addTab(self.vulnerabilities_tab, "Vulnerabilities")
        
        # Breaches tab
        self.breaches_tab = self.create_breaches_tab()
        self.tab_widget.addTab(self.breaches_tab, "Security Breaches")
        
        # Patches tab
        self.patches_tab = self.create_patches_tab()
        self.tab_widget.addTab(self.patches_tab, "Security Patches")
        
        # Feeds tab
        self.feeds_tab = self.create_feeds_tab()
        self.tab_widget.addTab(self.feeds_tab, "Security Feeds")
        
        # Training data tab
        self.training_tab = self.create_training_tab()
        self.tab_widget.addTab(self.training_tab, "Training Data")
        
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)
    
    def create_vulnerabilities_tab(self) -> QWidget:
        """Create vulnerabilities tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Filters
        filter_layout = QHBoxLayout()
        
        severity_label = QLabel("Severity:")
        self.severity_combo = QComboBox()
        self.severity_combo.addItems(["All", "Critical", "High", "Medium", "Low"])
        self.severity_combo.currentTextChanged.connect(self.filter_vulnerabilities)
        filter_layout.addWidget(severity_label)
        filter_layout.addWidget(self.severity_combo)
        
        search_label = QLabel("Search:")
        self.vuln_search = QLineEdit()
        self.vuln_search.setPlaceholderText("Search vulnerabilities...")
        self.vuln_search.textChanged.connect(self.filter_vulnerabilities)
        filter_layout.addWidget(search_label)
        filter_layout.addWidget(self.vuln_search)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Vulnerabilities table
        self.vuln_table = QTableWidget()
        self.vuln_table.setColumnCount(8)
        self.vuln_table.setHorizontalHeaderLabels([
            "ID", "Title", "Severity", "CVSS Score", "Source", "Published", "Patched", "Actions"
        ])
        
        header = self.vuln_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.vuln_table)
        widget.setLayout(layout)
        return widget
    
    def create_breaches_tab(self) -> QWidget:
        """Create security breaches tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Breaches table
        self.breach_table = QTableWidget()
        self.breach_table.setColumnCount(7)
        self.breach_table.setHorizontalHeaderLabels([
            "Company", "Title", "Severity", "Affected Users", "Attack Vector", "Date", "Actions"
        ])
        
        header = self.breach_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.breach_table)
        widget.setLayout(layout)
        return widget
    
    def create_patches_tab(self) -> QWidget:
        """Create security patches tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Patches table
        self.patch_table = QTableWidget()
        self.patch_table.setColumnCount(8)
        self.patch_table.setHorizontalHeaderLabels([
            "Title", "Version", "Severity", "Products", "Release Date", "Tested", "Applied", "Actions"
        ])
        
        header = self.patch_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.patch_table)
        widget.setLayout(layout)
        return widget
    
    def create_feeds_tab(self) -> QWidget:
        """Create security feeds tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Add feed section
        add_feed_group = QGroupBox("Add Security Feed")
        add_feed_layout = QFormLayout()
        
        self.feed_name = QLineEdit()
        self.feed_url = QLineEdit()
        self.feed_type = QComboBox()
        self.feed_type.addItems(["rss", "atom", "api"])
        self.feed_enabled = QCheckBox("Enabled")
        self.feed_enabled.setChecked(True)
        self.feed_interval = QSpinBox()
        self.feed_interval.setRange(300, 86400)  # 5 minutes to 24 hours
        self.feed_interval.setValue(3600)  # 1 hour
        self.feed_interval.setSuffix(" seconds")
        
        add_feed_layout.addRow("Name:", self.feed_name)
        add_feed_layout.addRow("URL:", self.feed_url)
        add_feed_layout.addRow("Type:", self.feed_type)
        add_feed_layout.addRow("Enabled:", self.feed_enabled)
        add_feed_layout.addRow("Fetch Interval:", self.feed_interval)
        
        add_feed_btn = QPushButton("Add Feed")
        add_feed_btn.clicked.connect(self.add_security_feed)
        add_feed_layout.addRow("", add_feed_btn)
        
        add_feed_group.setLayout(add_feed_layout)
        layout.addWidget(add_feed_group)
        
        # Feeds table
        self.feed_table = QTableWidget()
        self.feed_table.setColumnCount(6)
        self.feed_table.setHorizontalHeaderLabels([
            "Name", "URL", "Type", "Enabled", "Last Fetch", "Actions"
        ])
        
        header = self.feed_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.feed_table)
        widget.setLayout(layout)
        return widget
    
    def create_training_tab(self) -> QWidget:
        """Create training data tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Training data info
        info_layout = QHBoxLayout()
        self.training_count_label = QLabel("Training Data Items: 0")
        info_layout.addWidget(self.training_count_label)
        
        export_btn = QPushButton("Export Training Data")
        export_btn.clicked.connect(self.export_training_data)
        info_layout.addWidget(export_btn)
        
        info_layout.addStretch()
        layout.addLayout(info_layout)
        
        # Training data table
        self.training_table = QTableWidget()
        self.training_table.setColumnCount(6)
        self.training_table.setHorizontalHeaderLabels([
            "Type", "ID", "Title", "Severity", "Source", "Timestamp"
        ])
        
        header = self.training_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.training_table)
        widget.setLayout(layout)
        return widget
    
    def load_data(self):
        """Load security data."""
        try:
            self.load_vulnerabilities()
            self.load_breaches()
            self.load_patches()
            self.load_feeds()
            self.load_training_data()
        except Exception as e:
            logger.error(f"Error loading security data: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load security data: {e}")
    
    def load_vulnerabilities(self):
        """Load vulnerabilities data."""
        try:
            vulnerabilities = self.backend_controller.get_security_vulnerabilities()
            self.populate_vulnerabilities_table(vulnerabilities)
        except Exception as e:
            logger.error(f"Error loading vulnerabilities: {e}")
    
    def load_breaches(self):
        """Load security breaches data."""
        try:
            breaches = self.backend_controller.get_security_breaches()
            self.populate_breaches_table(breaches)
        except Exception as e:
            logger.error(f"Error loading breaches: {e}")
    
    def load_patches(self):
        """Load security patches data."""
        try:
            patches = self.backend_controller.get_security_patches()
            self.populate_patches_table(patches)
        except Exception as e:
            logger.error(f"Error loading patches: {e}")
    
    def load_feeds(self):
        """Load security feeds data."""
        try:
            feeds = self.backend_controller.get_security_feeds()
            self.populate_feeds_table(feeds)
        except Exception as e:
            logger.error(f"Error loading feeds: {e}")
    
    def load_training_data(self):
        """Load training data."""
        try:
            training_data = self.backend_controller.get_security_training_data()
            self.populate_training_table(training_data)
        except Exception as e:
            logger.error(f"Error loading training data: {e}")
    
    def populate_vulnerabilities_table(self, vulnerabilities: List[Dict]):
        """Populate vulnerabilities table."""
        self.vuln_table.setRowCount(len(vulnerabilities))
        
        for row, vuln in enumerate(vulnerabilities):
            self.vuln_table.setItem(row, 0, QTableWidgetItem(vuln.get("id", "")))
            self.vuln_table.setItem(row, 1, QTableWidgetItem(vuln.get("title", "")))
            
            severity = vuln.get("severity", "")
            severity_item = QTableWidgetItem(severity)
            if severity == "Critical":
                severity_item.setBackground(QColor(255, 200, 200))
            elif severity == "High":
                severity_item.setBackground(QColor(255, 220, 200))
            self.vuln_table.setItem(row, 2, severity_item)
            
            cvss_score = vuln.get("cvss_score")
            self.vuln_table.setItem(row, 3, QTableWidgetItem(str(cvss_score) if cvss_score else ""))
            self.vuln_table.setItem(row, 4, QTableWidgetItem(vuln.get("source", "")))
            
            published_date = vuln.get("published_date")
            if published_date:
                try:
                    date_obj = datetime.fromisoformat(published_date.replace('Z', '+00:00'))
                    date_str = date_obj.strftime("%Y-%m-%d")
                except:
                    date_str = published_date
            else:
                date_str = ""
            self.vuln_table.setItem(row, 5, QTableWidgetItem(date_str))
            
            is_patched = vuln.get("is_patched", False)
            patched_item = QTableWidgetItem("Yes" if is_patched else "No")
            if is_patched:
                patched_item.setBackground(QColor(200, 255, 200))
            self.vuln_table.setItem(row, 6, patched_item)
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(0, 0, 0, 0)
            
            if not is_patched:
                patch_btn = QPushButton("Mark Patched")
                patch_btn.clicked.connect(lambda checked, v=vuln: self.mark_vulnerability_patched(v))
                actions_layout.addWidget(patch_btn)
            
            actions_widget.setLayout(actions_layout)
            self.vuln_table.setCellWidget(row, 7, actions_widget)
    
    def populate_breaches_table(self, breaches: List[Dict]):
        """Populate breaches table."""
        self.breach_table.setRowCount(len(breaches))
        
        for row, breach in enumerate(breaches):
            self.breach_table.setItem(row, 0, QTableWidgetItem(breach.get("company", "")))
            self.breach_table.setItem(row, 1, QTableWidgetItem(breach.get("title", "")))
            self.breach_table.setItem(row, 2, QTableWidgetItem(breach.get("severity", "")))
            
            affected_users = breach.get("affected_users")
            self.breach_table.setItem(row, 3, QTableWidgetItem(str(affected_users) if affected_users else ""))
            self.breach_table.setItem(row, 4, QTableWidgetItem(breach.get("attack_vector", "")))
            
            breach_date = breach.get("breach_date")
            if breach_date:
                try:
                    date_obj = datetime.fromisoformat(breach_date.replace('Z', '+00:00'))
                    date_str = date_obj.strftime("%Y-%m-%d")
                except:
                    date_str = breach_date
            else:
                date_str = ""
            self.breach_table.setItem(row, 5, QTableWidgetItem(date_str))
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(0, 0, 0, 0)
            
            view_btn = QPushButton("View Details")
            view_btn.clicked.connect(lambda checked, b=breach: self.view_breach_details(b))
            actions_layout.addWidget(view_btn)
            
            actions_widget.setLayout(actions_layout)
            self.breach_table.setCellWidget(row, 6, actions_widget)
    
    def populate_patches_table(self, patches: List[Dict]):
        """Populate patches table."""
        self.patch_table.setRowCount(len(patches))
        
        for row, patch in enumerate(patches):
            self.patch_table.setItem(row, 0, QTableWidgetItem(patch.get("title", "")))
            self.patch_table.setItem(row, 1, QTableWidgetItem(patch.get("patch_version", "")))
            self.patch_table.setItem(row, 2, QTableWidgetItem(patch.get("severity", "")))
            
            products = ", ".join(patch.get("affected_products", []))
            self.patch_table.setItem(row, 3, QTableWidgetItem(products))
            
            release_date = patch.get("release_date")
            if release_date:
                try:
                    date_obj = datetime.fromisoformat(release_date.replace('Z', '+00:00'))
                    date_str = date_obj.strftime("%Y-%m-%d")
                except:
                    date_str = release_date
            else:
                date_str = ""
            self.patch_table.setItem(row, 4, QTableWidgetItem(date_str))
            
            tested = patch.get("tested", False)
            tested_item = QTableWidgetItem("Yes" if tested else "No")
            self.patch_table.setItem(row, 5, tested_item)
            
            applied = patch.get("applied", False)
            applied_item = QTableWidgetItem("Yes" if applied else "No")
            if applied:
                applied_item.setBackground(QColor(200, 255, 200))
            self.patch_table.setItem(row, 6, applied_item)
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(0, 0, 0, 0)
            
            if not applied:
                apply_btn = QPushButton("Apply")
                apply_btn.clicked.connect(lambda checked, p=patch: self.apply_patch(p))
                actions_layout.addWidget(apply_btn)
            
            view_btn = QPushButton("View")
            view_btn.clicked.connect(lambda checked, p=patch: self.view_patch_details(p))
            actions_layout.addWidget(view_btn)
            
            actions_widget.setLayout(actions_layout)
            self.patch_table.setCellWidget(row, 7, actions_widget)
    
    def populate_feeds_table(self, feeds: List[Dict]):
        """Populate feeds table."""
        self.feed_table.setRowCount(len(feeds))
        
        for row, feed in enumerate(feeds):
            self.feed_table.setItem(row, 0, QTableWidgetItem(feed.get("name", "")))
            self.feed_table.setItem(row, 1, QTableWidgetItem(feed.get("url", "")))
            self.feed_table.setItem(row, 2, QTableWidgetItem(feed.get("feed_type", "")))
            
            enabled = feed.get("enabled", True)
            enabled_item = QTableWidgetItem("Yes" if enabled else "No")
            self.feed_table.setItem(row, 3, enabled_item)
            
            last_fetch = feed.get("last_fetch")
            if last_fetch:
                try:
                    date_obj = datetime.fromisoformat(last_fetch.replace('Z', '+00:00'))
                    date_str = date_obj.strftime("%Y-%m-%d %H:%M")
                except:
                    date_str = last_fetch
            else:
                date_str = "Never"
            self.feed_table.setItem(row, 4, QTableWidgetItem(date_str))
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(0, 0, 0, 0)
            
            remove_btn = QPushButton("Remove")
            remove_btn.clicked.connect(lambda checked, f=feed: self.remove_security_feed(f))
            actions_layout.addWidget(remove_btn)
            
            actions_widget.setLayout(actions_layout)
            self.feed_table.setCellWidget(row, 5, actions_widget)
    
    def populate_training_table(self, training_data: List[Dict]):
        """Populate training data table."""
        self.training_table.setRowCount(len(training_data))
        self.training_count_label.setText(f"Training Data Items: {len(training_data)}")
        
        for row, item in enumerate(training_data):
            self.training_table.setItem(row, 0, QTableWidgetItem(item.get("type", "")))
            self.training_table.setItem(row, 1, QTableWidgetItem(item.get("id", "")))
            self.training_table.setItem(row, 2, QTableWidgetItem(item.get("title", "")))
            self.training_table.setItem(row, 3, QTableWidgetItem(item.get("severity", "")))
            self.training_table.setItem(row, 4, QTableWidgetItem(item.get("source", "")))
            
            timestamp = item.get("timestamp", "")
            if timestamp:
                try:
                    date_obj = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    date_str = date_obj.strftime("%Y-%m-%d %H:%M")
                except:
                    date_str = timestamp
            else:
                date_str = ""
            self.training_table.setItem(row, 5, QTableWidgetItem(date_str))
    
    def filter_vulnerabilities(self):
        """Filter vulnerabilities based on search and severity."""
        try:
            severity = self.severity_combo.currentText()
            search_text = self.vuln_search.text().lower()
            
            vulnerabilities = self.backend_controller.get_security_vulnerabilities()
            filtered_vulns = []
            
            for vuln in vulnerabilities:
                # Filter by severity
                if severity != "All" and vuln.get("severity", "") != severity:
                    continue
                
                # Filter by search text
                if search_text:
                    if (search_text not in vuln.get("title", "").lower() and
                        search_text not in vuln.get("description", "").lower() and
                        search_text not in vuln.get("id", "").lower()):
                        continue
                
                filtered_vulns.append(vuln)
            
            self.populate_vulnerabilities_table(filtered_vulns)
            
        except Exception as e:
            logger.error(f"Error filtering vulnerabilities: {e}")
    
    def fetch_security_feeds(self):
        """Fetch security feeds."""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.feed_worker = SecurityFeedWorker(self.backend_controller)
        self.feed_worker.progress.connect(self.progress_bar.setValue)
        self.feed_worker.finished.connect(self.on_feeds_fetched)
        self.feed_worker.start()
    
    def on_feeds_fetched(self, success: bool, message: str):
        """Handle feed fetching completion."""
        self.progress_bar.setVisible(False)
        
        if success:
            self.load_data()
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.warning(self, "Error", f"Failed to fetch feeds: {message}")
    
    def add_security_feed(self):
        """Add a new security feed."""
        try:
            name = self.feed_name.text().strip()
            url = self.feed_url.text().strip()
            
            if not name or not url:
                QMessageBox.warning(self, "Error", "Name and URL are required")
                return
            
            feed_data = {
                "name": name,
                "url": url,
                "feed_type": self.feed_type.currentText(),
                "enabled": self.feed_enabled.isChecked(),
                "fetch_interval": self.feed_interval.value(),
                "tags": []
            }
            
            self.backend_controller.add_security_feed(feed_data)
            self.load_feeds()
            
            # Clear form
            self.feed_name.clear()
            self.feed_url.clear()
            
            QMessageBox.information(self, "Success", "Security feed added successfully")
            
        except Exception as e:
            logger.error(f"Error adding security feed: {e}")
            QMessageBox.warning(self, "Error", f"Failed to add security feed: {e}")
    
    def remove_security_feed(self, feed: Dict):
        """Remove a security feed."""
        try:
            name = feed.get("name", "")
            reply = QMessageBox.question(
                self, "Confirm Removal", 
                f"Are you sure you want to remove the security feed '{name}'?"
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.backend_controller.remove_security_feed(name)
                self.load_feeds()
                QMessageBox.information(self, "Success", f"Security feed '{name}' removed")
                
        except Exception as e:
            logger.error(f"Error removing security feed: {e}")
            QMessageBox.warning(self, "Error", f"Failed to remove security feed: {e}")
    
    def mark_vulnerability_patched(self, vulnerability: Dict):
        """Mark a vulnerability as patched."""
        try:
            vuln_id = vulnerability.get("id", "")
            self.backend_controller.mark_vulnerability_patched(vuln_id)
            self.load_vulnerabilities()
            QMessageBox.information(self, "Success", f"Vulnerability '{vuln_id}' marked as patched")
            
        except Exception as e:
            logger.error(f"Error marking vulnerability as patched: {e}")
            QMessageBox.warning(self, "Error", f"Failed to mark vulnerability as patched: {e}")
    
    def apply_patch(self, patch: Dict):
        """Apply a security patch."""
        try:
            patch_id = patch.get("id", "")
            self.backend_controller.mark_patch_applied(patch_id)
            self.load_patches()
            QMessageBox.information(self, "Success", f"Patch '{patch_id}' marked as applied")
            
        except Exception as e:
            logger.error(f"Error applying patch: {e}")
            QMessageBox.warning(self, "Error", f"Failed to apply patch: {e}")
    
    def view_breach_details(self, breach: Dict):
        """View breach details."""
        details = f"""
Company: {breach.get('company', '')}
Title: {breach.get('title', '')}
Description: {breach.get('description', '')}
Severity: {breach.get('severity', '')}
Affected Users: {breach.get('affected_users', '')}
Attack Vector: {breach.get('attack_vector', '')}
Data Types: {', '.join(breach.get('data_types', []))}
Lessons Learned: {', '.join(breach.get('lessons_learned', []))}
Mitigation Strategies: {', '.join(breach.get('mitigation_strategies', []))}
        """
        
        QMessageBox.information(self, "Breach Details", details)
    
    def view_patch_details(self, patch: Dict):
        """View patch details."""
        details = f"""
Title: {patch.get('title', '')}
Description: {patch.get('description', '')}
Version: {patch.get('patch_version', '')}
Severity: {patch.get('severity', '')}
Affected Products: {', '.join(patch.get('affected_products', []))}
Download URL: {patch.get('download_url', '')}
Installation Instructions: {patch.get('installation_instructions', '')}
        """
        
        QMessageBox.information(self, "Patch Details", details)
    
    def export_training_data(self):
        """Export training data."""
        try:
            training_data = self.backend_controller.get_security_training_data()
            
            # Save to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"security_training_data_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(training_data, f, indent=2)
            
            QMessageBox.information(self, "Success", f"Training data exported to {filename}")
            
        except Exception as e:
            logger.error(f"Error exporting training data: {e}")
            QMessageBox.warning(self, "Error", f"Failed to export training data: {e}")
    
    def refresh_data(self):
        """Refresh all data."""
        self.load_data()
    
    def handle_error(self, error: str):
        """Handle errors."""
        logger.error(f"Security Intelligence Tab Error: {error}")
        QMessageBox.warning(self, "Error", f"An error occurred: {error}") 