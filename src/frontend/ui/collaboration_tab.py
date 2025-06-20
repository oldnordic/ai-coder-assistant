"""
Collaboration Features Tab - Clean, modern interface for team collaboration.
"""

import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Callable, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
    QLabel, QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QLineEdit, QFileDialog, QMessageBox, QTabWidget,
    QListWidget, QListWidgetItem, QProgressBar, QCheckBox, QDialog,
    QFormLayout, QDateEdit, QSpinBox, QDoubleSpinBox, QSplitter
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, pyqtBoundSignal
from PyQt6.QtGui import QFont, QColor, QIcon

# Import backend task management service
from backend.services.task_management import (
    get_task_management_service, TaskStatus, TaskPriority, Task
)

logger = logging.getLogger(__name__)


class PlatformConfig:
    """Configuration for collaboration platforms."""
    
    def __init__(self):
        self.teams_enabled = False
        self.teams_token = ""
        self.slack_enabled = False
        self.slack_token = ""
        self.github_enabled = False
        self.github_token = ""
    
    @property
    def has_active_platform(self) -> bool:
        return any([self.teams_enabled, self.slack_enabled, self.github_enabled])


class ConfigDialog(QDialog):
    """Dialog for configuring collaboration platforms."""
    
    def __init__(self, config: PlatformConfig, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.config = config
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Setup the configuration dialog UI."""
        self.setWindowTitle("Configure Collaboration Platforms")
        layout = QFormLayout(self)
        
        # Microsoft Teams
        self.teams_check = QCheckBox("Enable Microsoft Teams")
        self.teams_check.setChecked(self.config.teams_enabled)
        self.teams_token = QLineEdit(self.config.teams_token)
        self.teams_token.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow(self.teams_check)
        layout.addRow("Teams Token:", self.teams_token)
        
        # Slack
        self.slack_check = QCheckBox("Enable Slack")
        self.slack_check.setChecked(self.config.slack_enabled)
        self.slack_token = QLineEdit(self.config.slack_token)
        self.slack_token.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow(self.slack_check)
        layout.addRow("Slack Token:", self.slack_token)
        
        # GitHub
        self.github_check = QCheckBox("Enable GitHub")
        self.github_check.setChecked(self.config.github_enabled)
        self.github_token = QLineEdit(self.config.github_token)
        self.github_token.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow(self.github_check)
        layout.addRow("GitHub Token:", self.github_token)
        
        # Buttons
        button_box = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_config)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_box.addWidget(save_btn)
        button_box.addWidget(cancel_btn)
        layout.addRow(button_box)
    
    def save_config(self) -> None:
        """Save the configuration."""
        self.config.teams_enabled = self.teams_check.isChecked()
        self.config.teams_token = self.teams_token.text()
        self.config.slack_enabled = self.slack_check.isChecked()
        self.config.slack_token = self.slack_token.text()
        self.config.github_enabled = self.github_check.isChecked()
        self.config.github_token = self.github_token.text()
        self.accept()


class TeamMember:
    """Represents a team member."""
    
    def __init__(self, name: str, role: str, status: str = "online"):
        self.name = name
        self.role = role
        self.status = status
        self.last_seen: datetime = datetime.now()


class ChatMessage:
    """Represents a chat message."""
    
    def __init__(
        self,
        sender: str,
        content: str,
        message_type: str = "text",
        timestamp: Optional[datetime] = None
    ):
        self.sender = sender
        self.content = content
        self.message_type = message_type  # "text", "code", "file"
        self.timestamp = timestamp or datetime.now()
        self.id = f"{self.sender}_{self.timestamp.timestamp()}"


class TeamChatWidget(QWidget):
    """Widget for team chat functionality."""
    
    message_sent = pyqtSignal(str, str)  # sender, content
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.messages: List[ChatMessage] = []
        self.team_members = [
            TeamMember("Alice", "Senior Developer", "online"),
            TeamMember("Bob", "QA Engineer", "online"),
            TeamMember("Charlie", "DevOps Engineer", "away"),
            TeamMember("David", "Product Manager", "online"),
            TeamMember("Eva", "UI/UX Designer", "offline")
        ]
        self.current_user = "You"
        self.setup_ui()
        self.load_chat_history()
    
    def setup_ui(self) -> None:
        """Setup the chat UI."""
        layout = QVBoxLayout(self)
        
        # Header with team info
        header_layout = QHBoxLayout()
        
        # Online members indicator
        online_count = sum(1 for member in self.team_members if member.status == "online")
        status_label = QLabel(f"Team Chat ({online_count} online)")
        status_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header_layout.addWidget(status_label)
        
        # Team members dropdown
        self.members_combo = QComboBox()
        self.members_combo.addItems([member.name for member in self.team_members])
        self.members_combo.currentTextChanged.connect(self.change_user)
        header_layout.addWidget(QLabel("Act as:"))
        header_layout.addWidget(self.members_combo)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Chat area
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setMaximumHeight(300)
        self.chat_area.setStyleSheet("""
            QTextEdit {
                background-color: #2F2F2F;
                color: #CCCCCC;
                border: 1px solid #444444;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
            }
        """)
        layout.addWidget(self.chat_area)
        
        # Message input
        input_layout = QHBoxLayout()
        
        # Message type selector
        self.message_type_combo = QComboBox()
        self.message_type_combo.addItems(["Text", "Code Snippet", "File Share"])
        input_layout.addWidget(QLabel("Type:"))
        input_layout.addWidget(self.message_type_combo)
        
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your message...")
        self.message_input.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.message_input)
        
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)
        
        layout.addLayout(input_layout)
        
        # Add some sample messages
        self.add_sample_messages()
    
    def change_user(self, user_name: str):
        """Change the current user."""
        self.current_user = user_name
        self.log_message(f"Now acting as {user_name}")
    
    def send_message(self):
        """Send a message."""
        message = self.message_input.text().strip()
        if not message:
            return
        
        message_type = self.message_type_combo.currentText().lower()
        
        if message_type == "file share":
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select File to Share", "", "All Files (*)"
            )
            if file_path:
                message = f"📁 Shared file: {os.path.basename(file_path)}"
        
        timestamp = datetime.now().strftime("%H:%M")
        formatted_message = f"[{timestamp}] {self.current_user}: {message}"
        self.chat_area.append(formatted_message)
        self.message_input.clear()
        
        # Emit signal for other components
        self.message_sent.emit(self.current_user, message)
        
        # Simulate response
        QTimer.singleShot(1000, self.simulate_response)
    
    def simulate_response(self):
        """Simulate a team member response."""
        responses = [
            "Thanks for the update! I'll review that shortly.",
            "Great work! The implementation looks solid.",
            "I have some questions about the approach. Can we discuss?",
            "This looks good to me. Ready for testing.",
            "I'll help with the testing phase.",
            "Can you share the test results when ready?",
            "I'm working on a similar feature. Let's coordinate.",
            "The code review is complete. Minor suggestions in comments.",
            "Deployment looks successful. Monitoring in progress.",
            "I found a potential issue. Can you check line 45?"
        ]
        
        import random
        response = random.choice(responses)
        responder = random.choice([m for m in self.team_members if m.name != self.current_user])
        
        timestamp = datetime.now().strftime("%H:%M")
        formatted_response = f"[{timestamp}] {responder.name}: {response}"
        self.chat_area.append(formatted_response)
    
    def add_sample_messages(self):
        """Add sample messages to the chat."""
        sample_messages = [
            "[09:15] Alice: Good morning team! How's everyone doing?",
            "[09:16] Bob: Morning! I'm ready to start testing the new authentication system.",
            "[09:17] Charlie: DevOps here. The staging environment is ready for deployment.",
            "[09:18] David: Great! Let's aim to have the feature ready for demo by Friday.",
            "[09:20] Alice: Perfect! I'm almost done with the implementation. Should be ready for review by EOD.",
            "[09:22] Eva: I've updated the UI mockups based on the feedback. Check the Figma link I shared.",
            "[09:25] Bob: I'll start writing test cases for the new API endpoints.",
            "[09:30] Charlie: Database migration scripts are ready. I'll run them in staging first."
        ]
        
        for message in sample_messages:
            self.chat_area.append(message)
    
    def load_chat_history(self):
        """Load chat history from file (simulated)."""
        # In a real implementation, this would load from a database or file
        pass
    
    def log_message(self, message: str):
        """Log a system message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.chat_area.append(f"[{timestamp}] System: {message}")


class CodeSharingWidget(QWidget):
    """Widget for code sharing functionality."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.shared_items = []
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the code sharing UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Code Sharing & Collaboration")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Share controls
        controls_group = QGroupBox("Share New Item")
        controls_layout = QVBoxLayout(controls_group)
        
        # Share type selector
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Share Type:"))
        self.share_type_combo = QComboBox()
        self.share_type_combo.addItems(["File", "Code Snippet", "Documentation", "Configuration"])
        type_layout.addWidget(self.share_type_combo)
        controls_layout.addLayout(type_layout)
        
        # Share buttons
        button_layout = QHBoxLayout()
        
        self.share_file_button = QPushButton("Share File")
        self.share_file_button.clicked.connect(self.share_file)
        button_layout.addWidget(self.share_file_button)
        
        self.share_snippet_button = QPushButton("Share Code Snippet")
        self.share_snippet_button.clicked.connect(self.share_snippet)
        button_layout.addWidget(self.share_snippet_button)
        
        self.share_doc_button = QPushButton("Share Documentation")
        self.share_doc_button.clicked.connect(self.share_documentation)
        button_layout.addWidget(self.share_doc_button)
        
        controls_layout.addLayout(button_layout)
        layout.addWidget(controls_group)
        
        # Shared items list
        items_group = QGroupBox("Shared Items")
        items_layout = QVBoxLayout(items_group)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter by:"))
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "Files", "Code Snippets", "Documentation", "Configuration"])
        self.filter_combo.currentTextChanged.connect(self.filter_items)
        filter_layout.addWidget(self.filter_combo)
        filter_layout.addStretch()
        items_layout.addLayout(filter_layout)
        
        self.shared_items_list = QListWidget()
        self.shared_items_list.itemDoubleClicked.connect(self.view_item)
        items_layout.addWidget(self.shared_items_list)
        
        layout.addWidget(items_group)
        
        # Populate with sample items
        self.populate_shared_items()
    
    def share_file(self):
        """Share a file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select File to Share", "", "All Files (*)"
        )
        if file_path:
            item = {
                "type": "file",
                "name": os.path.basename(file_path),
                "path": file_path,
                "shared_by": "You",
                "shared_date": datetime.now(),
                "description": f"Shared file: {os.path.basename(file_path)}"
            }
            self.shared_items.append(item)
            self.add_item_to_list(item)
            QMessageBox.information(self, "Success", f"File shared: {os.path.basename(file_path)}")
    
    def share_snippet(self):
        """Share a code snippet."""
        from PyQt6.QtWidgets import QInputDialog
        snippet, ok = QInputDialog.getMultiLineText(
            self, "Share Code Snippet", 
            "Enter your code snippet:",
            "def example_function():\n    print('Hello, World!')"
        )
        if ok and snippet.strip():
            item = {
                "type": "snippet",
                "name": "Code Snippet",
                "content": snippet,
                "shared_by": "You",
                "shared_date": datetime.now(),
                "description": "Shared code snippet"
            }
            self.shared_items.append(item)
            self.add_item_to_list(item)
            QMessageBox.information(self, "Success", "Code snippet shared!")
    
    def share_documentation(self):
        """Share documentation."""
        from PyQt6.QtWidgets import QInputDialog
        doc_content, ok = QInputDialog.getMultiLineText(
            self, "Share Documentation", 
            "Enter documentation content:",
            "# API Documentation\n\n## Endpoints\n\n### GET /users\nReturns list of users..."
        )
        if ok and doc_content.strip():
            item = {
                "type": "documentation",
                "name": "Documentation",
                "content": doc_content,
                "shared_by": "You",
                "shared_date": datetime.now(),
                "description": "Shared documentation"
            }
            self.shared_items.append(item)
            self.add_item_to_list(item)
            QMessageBox.information(self, "Success", "Documentation shared!")
    
    def add_item_to_list(self, item):
        """Add an item to the shared items list."""
        icon_map = {
            "file": "📁",
            "snippet": "💻",
            "documentation": "📄",
            "configuration": "⚙️"
        }
        
        icon = icon_map.get(item["type"], "📎")
        date_str = item["shared_date"].strftime("%m-%d %H:%M")
        text = f"{icon} {item['name']} (shared by {item['shared_by']} on {date_str})"
        
        list_item = QListWidgetItem(text)
        list_item.setData(Qt.ItemDataRole.UserRole, item)
        self.shared_items_list.addItem(list_item)
    
    def filter_items(self):
        """Filter items by type."""
        filter_type = self.filter_combo.currentText().lower()
        self.shared_items_list.clear()
        
        for item in self.shared_items:
            if filter_type == "all" or item["type"] == filter_type:
                self.add_item_to_list(item)
    
    def view_item(self, item):
        """View a shared item."""
        data = item.data(Qt.ItemDataRole.UserRole)
        if not data:
            return
        
        if data["type"] == "file":
            QMessageBox.information(self, "File Info", f"File: {data['name']}\nPath: {data['path']}")
        else:
            # Show content in a dialog
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton
            dialog = QDialog(self)
            dialog.setWindowTitle(f"View {data['name']}")
            dialog.setGeometry(400, 300, 600, 400)
            
            layout = QVBoxLayout(dialog)
            text_edit = QTextEdit()
            text_edit.setPlainText(data.get("content", ""))
            text_edit.setReadOnly(True)
            layout.addWidget(text_edit)
            
            close_button = QPushButton("Close")
            close_button.clicked.connect(dialog.accept)
            layout.addWidget(close_button)
            
            dialog.exec()
    
    def populate_shared_items(self):
        """Populate with sample shared items."""
        sample_items = [
            {
                "type": "file",
                "name": "main.py",
                "path": "/path/to/main.py",
                "shared_by": "Alice",
                "shared_date": datetime.now() - timedelta(hours=2),
                "description": "Main application file"
            },
            {
                "type": "snippet",
                "name": "Database Connection",
                "content": "import psycopg2\n\ndef get_db_connection():\n    return psycopg2.connect(\n        host='localhost',\n        database='myapp',\n        user='user',\n        password='password'\n    )",
                "shared_by": "Bob",
                "shared_date": datetime.now() - timedelta(hours=1),
                "description": "Database connection utility"
            },
            {
                "type": "documentation",
                "name": "API Documentation",
                "content": "# REST API Documentation\n\n## Authentication\nAll API calls require a valid JWT token...",
                "shared_by": "Charlie",
                "shared_date": datetime.now() - timedelta(minutes=30),
                "description": "API documentation"
            },
            {
                "type": "configuration",
                "name": "Docker Configuration",
                "content": "FROM python:3.9\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install -r requirements.txt",
                "shared_by": "David",
                "shared_date": datetime.now() - timedelta(minutes=15),
                "description": "Dockerfile for deployment"
            }
        ]
        
        for item in sample_items:
            self.shared_items.append(item)
            self.add_item_to_list(item)


class ProjectManagementWidget(QWidget):
    """Widget for project management features with backend integration."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.task_service = get_task_management_service()
        self.setup_ui()
        self.load_tasks()
    
    def setup_ui(self):
        """Setup the project management UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Project Management")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Project overview
        overview_group = QGroupBox("Project Overview")
        overview_layout = QHBoxLayout(overview_group)
        
        # Progress indicators
        self.total_tasks_label = QLabel("Total: 0")
        self.completed_tasks_label = QLabel("Completed: 0")
        self.in_progress_label = QLabel("In Progress: 0")
        self.pending_label = QLabel("Pending: 0")
        self.overdue_label = QLabel("Overdue: 0")
        
        for label in [self.total_tasks_label, self.completed_tasks_label, 
                     self.in_progress_label, self.pending_label, self.overdue_label]:
            label.setStyleSheet("font-weight: bold; color: #007bff;")
            overview_layout.addWidget(label)
        
        overview_layout.addStretch()
        layout.addWidget(overview_group)
        
        # Task management
        task_group = QGroupBox("Add New Task")
        task_layout = QVBoxLayout(task_group)
        
        # Task input form
        form_layout = QHBoxLayout()
        form_layout.addWidget(QLabel("Title:"))
        self.task_title_input = QLineEdit()
        self.task_title_input.setPlaceholderText("Enter task title...")
        form_layout.addWidget(self.task_title_input)
        
        form_layout.addWidget(QLabel("Assignee:"))
        self.assignee_combo = QComboBox()
        self.assignee_combo.addItems(["You", "Alice", "Bob", "Charlie", "David", "Eva"])
        form_layout.addWidget(self.assignee_combo)
        
        form_layout.addWidget(QLabel("Priority:"))
        self.priority_combo = QComboBox()
        self.priority_combo.addItems([p.name for p in TaskPriority])
        form_layout.addWidget(self.priority_combo)
        
        self.add_task_button = QPushButton("Add Task")
        self.add_task_button.clicked.connect(self.add_task)
        form_layout.addWidget(self.add_task_button)
        
        task_layout.addLayout(form_layout)
        
        # Advanced task form
        advanced_layout = QHBoxLayout()
        advanced_layout.addWidget(QLabel("Description:"))
        self.task_description_input = QTextEdit()
        self.task_description_input.setMaximumHeight(60)
        self.task_description_input.setPlaceholderText("Enter task description...")
        advanced_layout.addWidget(self.task_description_input)
        
        advanced_layout.addWidget(QLabel("Due Date:"))
        self.due_date_edit = QDateEdit()
        self.due_date_edit.setDate(datetime.now().date())
        self.due_date_edit.setCalendarPopup(True)
        advanced_layout.addWidget(self.due_date_edit)
        
        advanced_layout.addWidget(QLabel("Est. Hours:"))
        self.estimated_hours_spin = QDoubleSpinBox()
        self.estimated_hours_spin.setRange(0.5, 100.0)
        self.estimated_hours_spin.setValue(4.0)
        self.estimated_hours_spin.setSuffix(" h")
        advanced_layout.addWidget(self.estimated_hours_spin)
        
        task_layout.addLayout(advanced_layout)
        layout.addWidget(task_group)
        
        # Tasks table
        table_group = QGroupBox("Tasks")
        table_layout = QVBoxLayout(table_group)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter by Status:"))
        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItems(["All"] + [s.name for s in TaskStatus])
        self.status_filter_combo.currentTextChanged.connect(self.filter_tasks)
        filter_layout.addWidget(self.status_filter_combo)
        
        filter_layout.addWidget(QLabel("Filter by Priority:"))
        self.priority_filter_combo = QComboBox()
        self.priority_filter_combo.addItems(["All"] + [p.name for p in TaskPriority])
        self.priority_filter_combo.currentTextChanged.connect(self.filter_tasks)
        filter_layout.addWidget(self.priority_filter_combo)
        
        filter_layout.addWidget(QLabel("Filter by Assignee:"))
        self.assignee_filter_combo = QComboBox()
        self.assignee_filter_combo.addItems(["All", "You", "Alice", "Bob", "Charlie", "David", "Eva"])
        self.assignee_filter_combo.currentTextChanged.connect(self.filter_tasks)
        filter_layout.addWidget(self.assignee_filter_combo)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_tasks)
        filter_layout.addWidget(refresh_btn)
        
        filter_layout.addStretch()
        table_layout.addLayout(filter_layout)
        
        self.tasks_table = QTableWidget()
        self.tasks_table.setColumnCount(8)
        self.tasks_table.setHorizontalHeaderLabels([
            "Title", "Assignee", "Status", "Priority", "Due Date", "Est. Hours", "Progress", "Actions"
        ])
        header = self.tasks_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        table_layout.addWidget(self.tasks_table)
        
        layout.addWidget(table_group)
    
    def add_task(self):
        """Add a new task using the backend service."""
        title = self.task_title_input.text().strip()
        if not title:
            QMessageBox.warning(self, "Missing Title", "Please enter a task title.")
            return
        
        description = self.task_description_input.toPlainText().strip()
        assignee = self.assignee_combo.currentText()
        priority = TaskPriority[self.priority_combo.currentText()]
        due_date = self.due_date_edit.date().toPyDate()
        estimated_hours = self.estimated_hours_spin.value()
        
        try:
            # Create task using backend service
            task = self.task_service.create_task(
                title=title,
                description=description,
                assignee=assignee,
                priority=priority,
                due_date=datetime.combine(due_date, datetime.min.time()),
                estimated_hours=estimated_hours,
                created_by="User"
            )
            
            # Clear form
            self.task_title_input.clear()
            self.task_description_input.clear()
            self.due_date_edit.setDate(datetime.now().date())
            self.estimated_hours_spin.setValue(4.0)
            
            # Refresh display
            self.load_tasks()
            
            QMessageBox.information(self, "Success", f"Task '{title}' created successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create task: {str(e)}")
    
    def load_tasks(self):
        """Load tasks from the backend service."""
        try:
            # Get all tasks from backend
            tasks = self.task_service.get_all_tasks()
            
            # Clear table
            self.tasks_table.setRowCount(0)
            
            # Add tasks to table
            for task in tasks:
                self.add_task_to_table(task)
            
            # Update overview
            self.update_overview()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load tasks: {str(e)}")
    
    def add_task_to_table(self, task: Task):
        """Add a task to the table."""
        row = self.tasks_table.rowCount()
        self.tasks_table.insertRow(row)
        
        # Title
        title_item = QTableWidgetItem(task.title)
        if task.description:
            title_item.setToolTip(task.description)
        self.tasks_table.setItem(row, 0, title_item)
        
        # Assignee
        self.tasks_table.setItem(row, 1, QTableWidgetItem(task.assignee))
        
        # Status
        status_item = QTableWidgetItem(task.status.value)
        if task.status == TaskStatus.DONE:
            status_item.setBackground(QColor(200, 255, 200))
        elif task.status == TaskStatus.IN_PROGRESS:
            status_item.setBackground(QColor(255, 255, 200))
        elif task.status == TaskStatus.REVIEW:
            status_item.setBackground(QColor(200, 200, 255))
        self.tasks_table.setItem(row, 2, status_item)
        
        # Priority
        priority_item = QTableWidgetItem(task.priority.value)
        priority_colors = {
            TaskPriority.CRITICAL.value: QColor(255, 200, 200),
            TaskPriority.HIGH.value: QColor(255, 220, 200),
            TaskPriority.MEDIUM.value: QColor(255, 255, 200),
            TaskPriority.LOW.value: QColor(200, 255, 200)
        }
        priority_item.setBackground(priority_colors.get(task.priority.value, QColor(255, 255, 255)))
        self.tasks_table.setItem(row, 3, priority_item)
        
        # Due Date
        due_date_text = task.due_date.strftime("%Y-%m-%d") if task.due_date else "No due date"
        due_date_item = QTableWidgetItem(due_date_text)
        if task.due_date and task.due_date < datetime.now() and task.status != TaskStatus.DONE:
            due_date_item.setBackground(QColor(255, 200, 200))  # Red for overdue
        self.tasks_table.setItem(row, 4, due_date_item)
        
        # Estimated Hours
        est_hours = f"{task.estimated_hours:.1f}h" if task.estimated_hours else "N/A"
        self.tasks_table.setItem(row, 5, QTableWidgetItem(est_hours))
        
        # Progress
        if task.estimated_hours and task.actual_hours:
            progress = min(100, (task.actual_hours / task.estimated_hours) * 100)
            progress_text = f"{progress:.0f}%"
        elif task.status == TaskStatus.DONE:
            progress_text = "100%"
        else:
            progress_text = "0%"
        self.tasks_table.setItem(row, 6, QTableWidgetItem(progress_text))
        
        # Actions
        actions_widget = QWidget()
        actions_layout = QHBoxLayout()
        actions_layout.setContentsMargins(0, 0, 0, 0)
        
        if task.status != TaskStatus.DONE:
            if task.status == TaskStatus.TODO:
                start_btn = QPushButton("Start")
                start_btn.clicked.connect(lambda: self.start_task(task.id))
                actions_layout.addWidget(start_btn)
            elif task.status == TaskStatus.IN_PROGRESS:
                complete_btn = QPushButton("Complete")
                complete_btn.clicked.connect(lambda: self.complete_task(task.id))
                actions_layout.addWidget(complete_btn)
        
        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(lambda: self.edit_task(task.id))
        actions_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(lambda: self.delete_task(task.id))
        actions_layout.addWidget(delete_btn)
        
        actions_widget.setLayout(actions_layout)
        self.tasks_table.setCellWidget(row, 7, actions_widget)
    
    def start_task(self, task_id: int):
        """Start a task (change status to In Progress)."""
        try:
            self.task_service.update_task(task_id, status=TaskStatus.IN_PROGRESS)
            self.load_tasks()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start task: {str(e)}")
    
    def complete_task(self, task_id: int):
        """Complete a task."""
        try:
            # For now, we'll use estimated hours as actual hours
            task = self.task_service.get_task(task_id)
            actual_hours = task.estimated_hours if task else None
            
            self.task_service.complete_task(task_id, actual_hours=actual_hours)
            self.load_tasks()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to complete task: {str(e)}")
    
    def edit_task(self, task_id: int):
        """Edit a task."""
        try:
            task = self.task_service.get_task(task_id)
            if not task:
                QMessageBox.warning(self, "Not Found", "Task not found.")
                return
            
            # Show edit dialog
            dialog = TaskEditDialog(task, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # Get updated data
                updated_data = dialog.get_updated_task_data()
                
                # Update task
                self.task_service.update_task(task_id, **updated_data)
                self.load_tasks()
                
                QMessageBox.information(self, "Success", "Task updated successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to edit task: {str(e)}")
    
    def delete_task(self, task_id: int):
        """Delete a task."""
        try:
            task = self.task_service.get_task(task_id)
            if not task:
                QMessageBox.warning(self, "Not Found", "Task not found.")
                return
            
            reply = QMessageBox.question(self, "Confirm Delete", 
                                       f"Are you sure you want to delete task '{task.title}'?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            
            if reply == QMessageBox.StandardButton.Yes:
                self.task_service.delete_task(task_id)
                self.load_tasks()
                QMessageBox.information(self, "Success", "Task deleted successfully.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete task: {str(e)}")
    
    def filter_tasks(self):
        """Filter tasks by status, priority, and assignee."""
        try:
            status_filter = self.status_filter_combo.currentText()
            priority_filter = self.priority_filter_combo.currentText()
            assignee_filter = self.assignee_filter_combo.currentText()
            
            # Get all tasks
            tasks = self.task_service.get_all_tasks()
            
            # Apply filters
            filtered_tasks = []
            for task in tasks:
                if status_filter != "All" and task.status.value != status_filter:
                    continue
                if priority_filter != "All" and task.priority.value != priority_filter:
                    continue
                if assignee_filter != "All" and task.assignee != assignee_filter:
                    continue
                filtered_tasks.append(task)
            
            # Update table
            self.tasks_table.setRowCount(0)
            for task in filtered_tasks:
                self.add_task_to_table(task)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to filter tasks: {str(e)}")
    
    def update_overview(self):
        """Update the project overview with analytics."""
        try:
            analytics = self.task_service.get_analytics()
            
            self.total_tasks_label.setText(f"Total: {analytics.total_tasks}")
            self.completed_tasks_label.setText(f"Completed: {analytics.completed_tasks}")
            self.in_progress_label.setText(f"In Progress: {analytics.in_progress_tasks}")
            self.pending_label.setText(f"Pending: {analytics.total_tasks - analytics.completed_tasks - analytics.in_progress_tasks}")
            self.overdue_label.setText(f"Overdue: {analytics.overdue_tasks}")
            
        except Exception as e:
            logger.error(f"Failed to update overview: {e}")


class TaskEditDialog(QDialog):
    """Dialog for editing task details."""
    
    def __init__(self, task: Task, parent=None):
        super().__init__(parent)
        self.task = task
        self.setup_ui()
        self.load_task_data()
    
    def setup_ui(self):
        """Setup the dialog UI."""
        self.setWindowTitle("Edit Task")
        self.setModal(True)
        self.resize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # Form layout
        form_layout = QFormLayout()
        
        # Title
        self.title_edit = QLineEdit()
        form_layout.addRow("Title:", self.title_edit)
        
        # Description
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        form_layout.addRow("Description:", self.description_edit)
        
        # Assignee
        self.assignee_combo = QComboBox()
        self.assignee_combo.addItems(["You", "Alice", "Bob", "Charlie", "David", "Eva"])
        form_layout.addRow("Assignee:", self.assignee_combo)
        
        # Status
        self.status_combo = QComboBox()
        self.status_combo.addItems([s.name for s in TaskStatus])
        form_layout.addRow("Status:", self.status_combo)
        
        # Priority
        self.priority_combo = QComboBox()
        self.priority_combo.addItems([p.name for p in TaskPriority])
        form_layout.addRow("Priority:", self.priority_combo)
        
        # Due Date
        self.due_date_edit = QDateEdit()
        self.due_date_edit.setCalendarPopup(True)
        form_layout.addRow("Due Date:", self.due_date_edit)
        
        # Estimated Hours
        self.estimated_hours_spin = QDoubleSpinBox()
        self.estimated_hours_spin.setRange(0.5, 100.0)
        self.estimated_hours_spin.setSuffix(" h")
        form_layout.addRow("Estimated Hours:", self.estimated_hours_spin)
        
        # Actual Hours
        self.actual_hours_spin = QDoubleSpinBox()
        self.actual_hours_spin.setRange(0.0, 100.0)
        self.actual_hours_spin.setSuffix(" h")
        form_layout.addRow("Actual Hours:", self.actual_hours_spin)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
    
    def load_task_data(self):
        """Load current task data into the form."""
        self.title_edit.setText(self.task.title)
        self.description_edit.setPlainText(self.task.description)
        
        # Set assignee
        index = self.assignee_combo.findText(self.task.assignee)
        if index >= 0:
            self.assignee_combo.setCurrentIndex(index)
        
        # Set status
        index = self.status_combo.findText(self.task.status.value)
        if index >= 0:
            self.status_combo.setCurrentIndex(index)
        
        # Set priority
        index = self.priority_combo.findText(self.task.priority.value)
        if index >= 0:
            self.priority_combo.setCurrentIndex(index)
        
        # Set due date
        if self.task.due_date:
            self.due_date_edit.setDate(self.task.due_date.date())
        
        # Set hours
        if self.task.estimated_hours:
            self.estimated_hours_spin.setValue(self.task.estimated_hours)
        if self.task.actual_hours:
            self.actual_hours_spin.setValue(self.task.actual_hours)
    
    def get_updated_task_data(self) -> Dict[str, Any]:
        """Get the updated task data from the form."""
        return {
            "title": self.title_edit.text().strip(),
            "description": self.description_edit.toPlainText().strip(),
            "assignee": self.assignee_combo.currentText(),
            "status": TaskStatus[self.status_combo.currentText()],
            "priority": TaskPriority[self.priority_combo.currentText()],
            "due_date": datetime.combine(self.due_date_edit.date().toPyDate(), datetime.min.time()),
            "estimated_hours": self.estimated_hours_spin.value(),
            "actual_hours": self.actual_hours_spin.value()
        }


class CollaborationTab(QWidget):
    """Main Collaboration Features tab with clean, modern design."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.config = PlatformConfig()
        self.setup_ui()
        self.apply_styles()
    
    def setup_ui(self) -> None:
        """Setup the main UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header with title and configuration
        header_layout = QHBoxLayout()
        
        # Title
        title = QLabel("Collaboration Features")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        header_layout.addWidget(title)
        
        # Configuration button
        config_btn = QPushButton("Configure Platforms")
        config_btn.clicked.connect(self.show_config_dialog)
        header_layout.addWidget(config_btn)
        
        layout.addLayout(header_layout)
        
        # Platform status
        self.status_label = QLabel()
        self.update_status_label()
        layout.addWidget(self.status_label)
        
        # Description
        description = QLabel(
            "Team collaboration tools for code sharing, communication, and project management."
        )
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Tab widget for different collaboration features
        self.tab_widget = QTabWidget()
        
        # Team Chat Tab
        self.chat_widget = TeamChatWidget()
        self.tab_widget.addTab(self.chat_widget, "Team Chat")
        
        # Code Sharing Tab
        self.sharing_widget = CodeSharingWidget()
        self.tab_widget.addTab(self.sharing_widget, "Code Sharing")
        
        # Project Management Tab
        self.project_widget = ProjectManagementWidget()
        self.tab_widget.addTab(self.project_widget, "Project Management")
        
        layout.addWidget(self.tab_widget)
    
    def show_config_dialog(self) -> None:
        """Show the platform configuration dialog."""
        dialog = ConfigDialog(self.config, self)
        if dialog.exec():
            self.update_status_label()
            self.update_platform_integration()
    
    def update_status_label(self) -> None:
        """Update the platform status label."""
        status_text = "Active Platforms: "
        platforms = []
        if self.config.teams_enabled:
            platforms.append("Microsoft Teams")
        if self.config.slack_enabled:
            platforms.append("Slack")
        if self.config.github_enabled:
            platforms.append("GitHub")
        
        if platforms:
            status_text += ", ".join(platforms)
        else:
            status_text += "None (Configure platforms to enable integration)"
        
        self.status_label.setText(status_text)
    
    def update_platform_integration(self) -> None:
        """Update the integration with enabled platforms."""
        if not self.config.has_active_platform:
            QMessageBox.warning(
                self,
                "No Active Platforms",
                "Please configure and enable at least one collaboration platform."
            )
            return
        
        # TODO: Initialize platform clients and connect to services
        pass
    
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
            QLineEdit {
                padding: 8px;
                border: 1px solid #444444;
                border-radius: 4px;
                background: #2F2F2F;
                color: #CCCCCC;
            }
            QLineEdit:focus {
                border-color: #007bff;
                outline: none;
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
            QListWidget {
                border: 1px solid #444444;
                border-radius: 4px;
                background: #2F2F2F;
                color: #CCCCCC;
                padding: 4px;
            }
            QListWidget::item {
                padding: 4px;
                border-bottom: 1px solid #444444;
                color: #CCCCCC;
            }
            QListWidget::item:selected {
                background-color: #3F3F3F;
                color: #CCCCCC;
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