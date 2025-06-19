"""
Advanced Analytics Tab - Clean, modern interface for analytics and metrics.
"""

import logging
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
    QLabel, QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QFileDialog, QMessageBox, QTabWidget
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor

logger = logging.getLogger(__name__)


class MetricsWidget(QWidget):
    """Widget for displaying key metrics."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_metrics)
        self.update_timer.start(5000)  # Update every 5 seconds
    
    def setup_ui(self):
        """Setup the metrics UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Key Developer Metrics")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Metrics grid
        metrics_layout = QHBoxLayout()
        
        # Code Quality Metrics
        quality_group = QGroupBox("Code Quality")
        quality_layout = QVBoxLayout(quality_group)
        
        self.code_quality_score = QLabel("85%")
        self.code_quality_score.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        self.code_quality_score.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.code_quality_score.setStyleSheet("color: green;")
        quality_layout.addWidget(self.code_quality_score)
        
        quality_layout.addWidget(QLabel("Code Quality Score"))
        metrics_layout.addWidget(quality_group)
        
        # Performance Metrics
        perf_group = QGroupBox("Performance")
        perf_layout = QVBoxLayout(perf_group)
        
        self.performance_score = QLabel("92%")
        self.performance_score.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        self.performance_score.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.performance_score.setStyleSheet("color: blue;")
        perf_layout.addWidget(self.performance_score)
        
        perf_layout.addWidget(QLabel("Performance Score"))
        metrics_layout.addWidget(perf_group)
        
        # Security Metrics
        security_group = QGroupBox("Security")
        security_layout = QVBoxLayout(security_group)
        
        self.security_score = QLabel("78%")
        self.security_score.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        self.security_score.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.security_score.setStyleSheet("color: orange;")
        security_layout.addWidget(self.security_score)
        
        security_layout.addWidget(QLabel("Security Score"))
        metrics_layout.addWidget(security_group)
        
        layout.addLayout(metrics_layout)
    
    def update_metrics(self):
        """Update metrics display."""
        try:
            # Simulate metric updates
            import random
            self.code_quality_score.setText(f"{random.randint(80, 95)}%")
            self.performance_score.setText(f"{random.randint(85, 98)}%")
            self.security_score.setText(f"{random.randint(75, 90)}%")
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")


class TrendsWidget(QWidget):
    """Widget for displaying trends and analytics."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the trends UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Trends & Analytics")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Time period selector
        period_layout = QHBoxLayout()
        period_layout.addWidget(QLabel("Time Period:"))
        self.period_combo = QComboBox()
        self.period_combo.addItems(["Last 7 days", "Last 30 days", "Last 90 days", "Last year"])
        period_layout.addWidget(self.period_combo)
        period_layout.addStretch()
        layout.addLayout(period_layout)
        
        # Trends table
        self.trends_table = QTableWidget()
        self.trends_table.setColumnCount(4)
        self.trends_table.setHorizontalHeaderLabels([
            "Metric", "Current", "Previous", "Trend"
        ])
        header = self.trends_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.trends_table)
        
        # Populate with sample data
        self.populate_trends()
    
    def populate_trends(self):
        """Populate trends table with sample data."""
        trends_data = [
            ("Code Quality", "85%", "82%", "↗ Improving"),
            ("Performance", "92%", "89%", "↗ Improving"),
            ("Security", "78%", "75%", "↗ Improving"),
            ("Test Coverage", "87%", "85%", "↗ Improving"),
            ("Documentation", "72%", "70%", "↗ Improving"),
            ("Code Reviews", "95%", "93%", "↗ Improving")
        ]
        
        self.trends_table.setRowCount(len(trends_data))
        for i, (metric, current, previous, trend) in enumerate(trends_data):
            self.trends_table.setItem(i, 0, QTableWidgetItem(metric))
            self.trends_table.setItem(i, 1, QTableWidgetItem(current))
            self.trends_table.setItem(i, 2, QTableWidgetItem(previous))
            
            trend_item = QTableWidgetItem(trend)
            if "Improving" in trend:
                trend_item.setForeground(QColor("green"))
            elif "Declining" in trend:
                trend_item.setForeground(QColor("red"))
            else:
                trend_item.setForeground(QColor("orange"))
            
            self.trends_table.setItem(i, 3, trend_item)


class ReportsWidget(QWidget):
    """Widget for generating and viewing reports."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the reports UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Reports & Insights")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Report controls
        controls_layout = QHBoxLayout()
        
        controls_layout.addWidget(QLabel("Report Type:"))
        self.report_combo = QComboBox()
        self.report_combo.addItems([
            "Code Quality Report",
            "Performance Analysis",
            "Security Assessment",
            "Team Productivity",
            "Project Overview"
        ])
        controls_layout.addWidget(self.report_combo)
        
        self.generate_button = QPushButton("Generate Report")
        self.generate_button.clicked.connect(self.generate_report)
        controls_layout.addWidget(self.generate_button)
        
        self.export_button = QPushButton("Export")
        self.export_button.clicked.connect(self.export_report)
        self.export_button.setEnabled(False)
        controls_layout.addWidget(self.export_button)
        
        layout.addLayout(controls_layout)
        
        # Report content
        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        layout.addWidget(self.report_text)
    
    def generate_report(self):
        """Generate a report."""
        report_type = self.report_combo.currentText()
        
        # Simulate report generation
        self.generate_button.setEnabled(False)
        self.generate_button.setText("Generating...")
        
        # Simulate processing time
        QTimer.singleShot(2000, lambda: self.finish_report_generation(report_type))
    
    def finish_report_generation(self, report_type: str):
        """Finish report generation."""
        self.generate_button.setEnabled(True)
        self.generate_button.setText("Generate Report")
        self.export_button.setEnabled(True)
        
        # Sample report content
        report_content = f"""
# {report_type}
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary
This report provides insights into the current state of the codebase and development practices.

## Key Findings
- Overall code quality is improving
- Performance metrics show positive trends
- Security vulnerabilities have been reduced
- Team productivity is on track

## Recommendations
1. Continue with current development practices
2. Focus on improving test coverage
3. Maintain security awareness
4. Regular code reviews are effective

## Detailed Metrics
- Code Quality Score: 85%
- Performance Score: 92%
- Security Score: 78%
- Test Coverage: 87%

## Next Steps
- Implement automated testing improvements
- Enhance security scanning
- Optimize performance bottlenecks
- Improve documentation coverage
        """
        
        self.report_text.setPlainText(report_content)
    
    def export_report(self):
        """Export the report."""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export Report", "", "Text Files (*.txt);;JSON Files (*.json);;All Files (*)"
            )
            if file_path:
                content = self.report_text.toPlainText()
                with open(file_path, 'w') as f:
                    f.write(content)
                QMessageBox.information(self, "Success", f"Report exported to {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error exporting report: {e}")


class AdvancedAnalyticsTab(QWidget):
    """Main Advanced Analytics tab with clean, modern design."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.apply_styles()
    
    def setup_ui(self):
        """Setup the main UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Advanced Analytics")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Description
        description = QLabel(
            "Comprehensive analytics and insights for code quality, performance, and team productivity."
        )
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Tab widget for different analytics features
        self.tab_widget = QTabWidget()
        
        # Metrics Tab
        self.metrics_widget = MetricsWidget()
        self.tab_widget.addTab(self.metrics_widget, "Key Metrics")
        
        # Trends Tab
        self.trends_widget = TrendsWidget()
        self.tab_widget.addTab(self.trends_widget, "Trends")
        
        # Reports Tab
        self.reports_widget = ReportsWidget()
        self.tab_widget.addTab(self.reports_widget, "Reports")
        
        layout.addWidget(self.tab_widget)
    
    def apply_styles(self):
        """Apply modern styling."""
        self.setStyleSheet("""
            QWidget {
                background-color: #1F1F1F;
                color: #CCCCCC;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #444444;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background: #2F2F2F;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #CCCCCC;
            }
            QPushButton {
                background-color: #007bff;
                color: #CCCCCC;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
            QComboBox {
                padding: 8px;
                border: 1px solid #444444;
                border-radius: 4px;
                background: #2F2F2F;
                color: #CCCCCC;
            }
            QComboBox:focus {
                border-color: #007bff;
                outline: none;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #CCCCCC;
            }
            QTextEdit {
                border: 1px solid #444444;
                border-radius: 4px;
                background: #2F2F2F;
                color: #CCCCCC;
                padding: 8px;
            }
            QTableWidget {
                border: 1px solid #444444;
                border-radius: 4px;
                background: #2F2F2F;
                color: #CCCCCC;
                gridline-color: #444444;
            }
            QTableWidget::item {
                padding: 4px;
                color: #CCCCCC;
            }
            QTableWidget::item:selected {
                background-color: #3F3F3F;
                color: #CCCCCC;
            }
            QHeaderView::section {
                background-color: #1F1F1F;
                color: #CCCCCC;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #444444;
                font-weight: bold;
            }
            QTabWidget::pane {
                border: 1px solid #444444;
                background: #1F1F1F;
            }
            QTabBar::tab {
                background: #2F2F2F;
                color: #CCCCCC;
                padding: 8px 16px;
                border: 1px solid #444444;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #1F1F1F;
                border-bottom: 1px solid #1F1F1F;
            }
            QTabBar::tab:hover {
                background: #3F3F3F;
            }
        """) 