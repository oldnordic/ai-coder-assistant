"""
Collaboration Features Tab - Clean, modern interface for team collaboration.
"""

import logging
import json
import os
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
    QLabel, QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QLineEdit, QFileDialog, QMessageBox, QTabWidget,
    QListWidget, QListWidgetItem, QProgressBar, QCheckBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QIcon

logger = logging.getLogger(__name__)


class TeamMember:
    """Represents a team member."""
    
    def __init__(self, name: str, role: str, status: str = "online"):
        self.name = name
        self.role = role
        self.status = status
        self.last_seen = datetime.now()


class ChatMessage:
    """Represents a chat message."""
    
    def __init__(self, sender: str, content: str, message_type: str = "text", timestamp: datetime = None):
        self.sender = sender
        self.content = content
        self.message_type = message_type  # "text", "code", "file"
        self.timestamp = timestamp or datetime.now()
        self.id = f"{self.sender}_{self.timestamp.timestamp()}"


class TeamChatWidget(QWidget):
    """Widget for team chat functionality."""
    
    message_sent = pyqtSignal(str, str)  # sender, content
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.messages = []
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
    
    def setup_ui(self):
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
    """Widget for project management features."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tasks = []
        self.setup_ui()
    
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
        
        for label in [self.total_tasks_label, self.completed_tasks_label, 
                     self.in_progress_label, self.pending_label]:
            label.setStyleSheet("font-weight: bold; color: #007bff;")
            overview_layout.addWidget(label)
        
        overview_layout.addStretch()
        layout.addWidget(overview_group)
        
        # Task management
        task_group = QGroupBox("Add New Task")
        task_layout = QVBoxLayout(task_group)
        
        # Task input form
        form_layout = QHBoxLayout()
        form_layout.addWidget(QLabel("Task:"))
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("Enter task description...")
        form_layout.addWidget(self.task_input)
        
        form_layout.addWidget(QLabel("Assignee:"))
        self.assignee_combo = QComboBox()
        self.assignee_combo.addItems(["You", "Alice", "Bob", "Charlie", "David", "Eva"])
        form_layout.addWidget(self.assignee_combo)
        
        form_layout.addWidget(QLabel("Priority:"))
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["Low", "Medium", "High", "Critical"])
        form_layout.addWidget(self.priority_combo)
        
        self.add_task_button = QPushButton("Add Task")
        self.add_task_button.clicked.connect(self.add_task)
        form_layout.addWidget(self.add_task_button)
        
        task_layout.addLayout(form_layout)
        layout.addWidget(task_group)
        
        # Tasks table
        table_group = QGroupBox("Tasks")
        table_layout = QVBoxLayout(table_group)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter by Status:"))
        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItems(["All", "To Do", "In Progress", "Done"])
        self.status_filter_combo.currentTextChanged.connect(self.filter_tasks)
        filter_layout.addWidget(self.status_filter_combo)
        
        filter_layout.addWidget(QLabel("Filter by Priority:"))
        self.priority_filter_combo = QComboBox()
        self.priority_filter_combo.addItems(["All", "Low", "Medium", "High", "Critical"])
        self.priority_filter_combo.currentTextChanged.connect(self.filter_tasks)
        filter_layout.addWidget(self.priority_filter_combo)
        
        filter_layout.addStretch()
        table_layout.addLayout(filter_layout)
        
        self.tasks_table = QTableWidget()
        self.tasks_table.setColumnCount(5)
        self.tasks_table.setHorizontalHeaderLabels([
            "Task", "Assignee", "Status", "Priority", "Actions"
        ])
        header = self.tasks_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        table_layout.addWidget(self.tasks_table)
        
        layout.addWidget(table_group)
        
        # Populate with sample tasks
        self.populate_tasks()
        self.update_overview()
    
    def add_task(self):
        """Add a new task."""
        task = self.task_input.text().strip()
        if not task:
            return
        
        assignee = self.assignee_combo.currentText()
        priority = self.priority_combo.currentText()
        
        task_data = {
            "id": len(self.tasks) + 1,
            "description": task,
            "assignee": assignee,
            "status": "To Do",
            "priority": priority,
            "created_date": datetime.now(),
            "completed_date": None
        }
        
        self.tasks.append(task_data)
        self.add_task_to_table(task_data)
        self.task_input.clear()
        self.update_overview()
    
    def add_task_to_table(self, task):
        """Add a task to the table."""
        row = self.tasks_table.rowCount()
        self.tasks_table.insertRow(row)
        
        # Task description
        self.tasks_table.setItem(row, 0, QTableWidgetItem(task["description"]))
        
        # Assignee
        self.tasks_table.setItem(row, 1, QTableWidgetItem(task["assignee"]))
        
        # Status
        status_item = QTableWidgetItem(task["status"])
        if task["status"] == "Done":
            status_item.setBackground(QColor(200, 255, 200))
        elif task["status"] == "In Progress":
            status_item.setBackground(QColor(255, 255, 200))
        self.tasks_table.setItem(row, 2, status_item)
        
        # Priority
        priority_item = QTableWidgetItem(task["priority"])
        priority_colors = {
            "Critical": QColor(255, 200, 200),
            "High": QColor(255, 220, 200),
            "Medium": QColor(255, 255, 200),
            "Low": QColor(200, 255, 200)
        }
        priority_item.setBackground(priority_colors.get(task["priority"], QColor(255, 255, 255)))
        self.tasks_table.setItem(row, 3, priority_item)
        
        # Actions
        actions_widget = QWidget()
        actions_layout = QHBoxLayout()
        actions_layout.setContentsMargins(0, 0, 0, 0)
        
        if task["status"] != "Done":
            complete_btn = QPushButton("Complete")
            complete_btn.clicked.connect(lambda: self.complete_task(task["id"]))
            actions_layout.addWidget(complete_btn)
        
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(lambda: self.delete_task(task["id"]))
        actions_layout.addWidget(delete_btn)
        
        actions_widget.setLayout(actions_layout)
        self.tasks_table.setCellWidget(row, 4, actions_widget)
    
    def complete_task(self, task_id: int):
        """Mark a task as complete."""
        for task in self.tasks:
            if task["id"] == task_id:
                task["status"] = "Done"
                task["completed_date"] = datetime.now()
                break
        
        self.refresh_table()
        self.update_overview()
    
    def delete_task(self, task_id: int):
        """Delete a task."""
        self.tasks = [task for task in self.tasks if task["id"] != task_id]
        self.refresh_table()
        self.update_overview()
    
    def filter_tasks(self):
        """Filter tasks by status and priority."""
        self.refresh_table()
    
    def refresh_table(self):
        """Refresh the tasks table."""
        self.tasks_table.setRowCount(0)
        
        status_filter = self.status_filter_combo.currentText()
        priority_filter = self.priority_filter_combo.currentText()
        
        for task in self.tasks:
            if status_filter != "All" and task["status"] != status_filter:
                continue
            if priority_filter != "All" and task["priority"] != priority_filter:
                continue
            
            self.add_task_to_table(task)
    
    def update_overview(self):
        """Update the project overview."""
        total = len(self.tasks)
        completed = sum(1 for task in self.tasks if task["status"] == "Done")
        in_progress = sum(1 for task in self.tasks if task["status"] == "In Progress")
        pending = total - completed - in_progress
        
        self.total_tasks_label.setText(f"Total: {total}")
        self.completed_tasks_label.setText(f"Completed: {completed}")
        self.in_progress_label.setText(f"In Progress: {in_progress}")
        self.pending_label.setText(f"Pending: {pending}")
    
    def populate_tasks(self):
        """Populate with sample tasks."""
        sample_tasks = [
            {
                "id": 1,
                "description": "Implement user authentication system",
                "assignee": "Alice",
                "status": "In Progress",
                "priority": "High",
                "created_date": datetime.now() - timedelta(days=2),
                "completed_date": None
            },
            {
                "id": 2,
                "description": "Fix database connection timeout issue",
                "assignee": "Bob",
                "status": "Done",
                "priority": "Medium",
                "created_date": datetime.now() - timedelta(days=3),
                "completed_date": datetime.now() - timedelta(days=1)
            },
            {
                "id": 3,
                "description": "Add comprehensive unit tests",
                "assignee": "Charlie",
                "status": "To Do",
                "priority": "High",
                "created_date": datetime.now() - timedelta(days=1),
                "completed_date": None
            },
            {
                "id": 4,
                "description": "Update API documentation",
                "assignee": "David",
                "status": "To Do",
                "priority": "Low",
                "created_date": datetime.now() - timedelta(hours=6),
                "completed_date": None
            },
            {
                "id": 5,
                "description": "Optimize database queries",
                "assignee": "Alice",
                "status": "In Progress",
                "priority": "Medium",
                "created_date": datetime.now() - timedelta(hours=12),
                "completed_date": None
            }
        ]
        
        self.tasks = sample_tasks
        for task in self.tasks:
            self.add_task_to_table(task)


class CollaborationTab(QWidget):
    """Main Collaboration Features tab with clean, modern design."""
    
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
        title = QLabel("Collaboration Features")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
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