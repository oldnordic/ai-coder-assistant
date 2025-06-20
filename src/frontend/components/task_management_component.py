"""Task Management UI component for AI Coder Assistant."""

from typing import Optional
from PyQt6.QtWidgets import QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QListWidget
from PyQt6.QtCore import pyqtSlot

from frontend.components.base_component import BaseComponent, ComponentState
from core.events import Event, EventType
from core.logging import LogManager
from core.error import ErrorSeverity

class TaskManagementComponent(BaseComponent):
    """UI component for managing tasks (create/update/status/scheduling)."""
    def __init__(self, parent: Optional[object] = None):
        super().__init__(parent)
        self._logger = LogManager().get_logger("TaskManagementComponent")
        self._setup_ui()
        self.subscribe_to_event(EventType.TASK_STARTED, self.on_task_started)
        self.subscribe_to_event(EventType.TASK_COMPLETED, self.on_task_completed)
        self.subscribe_to_event(EventType.TASK_FAILED, self.on_task_failed)
        self.subscribe_to_event(EventType.TASK_CANCELLED, self.on_task_cancelled)
        self.tasks = []

    def _setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.status_label = QLabel("Task Management Ready.")
        self.task_list = QListWidget()
        self.create_task_button = QPushButton("Create Task")
        self.schedule_tasks_button = QPushButton("Schedule Tasks")
        self.create_task_button.clicked.connect(self.create_task)
        self.schedule_tasks_button.clicked.connect(self.schedule_tasks)
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.create_task_button)
        button_layout.addWidget(self.schedule_tasks_button)
        self.layout.addWidget(self.status_label)
        self.layout.addWidget(self.task_list)
        self.layout.addLayout(button_layout)
        self.setLayout(self.layout)

    @pyqtSlot()
    def create_task(self):
        self.status_label.setText("Creating task...")
        self.state = ComponentState.ACTIVATING
        self.publish_event(Event(type=EventType.TASK_STARTED, data={"action": "create"}))

    @pyqtSlot()
    def schedule_tasks(self):
        self.status_label.setText("Scheduling tasks...")
        self.state = ComponentState.ACTIVATING
        self.publish_event(Event(type=EventType.TASK_STARTED, data={"action": "schedule"}))

    def on_task_started(self, event: Event):
        action = event.data.get("action", "unknown") if event.data else "unknown"
        self.status_label.setText(f"Task {action} started...")
        self.state = ComponentState.ACTIVATING
        self._logger.info(f"Task {action} started")

    def on_task_completed(self, event: Event):
        task_id = event.data.get("task_id", "?") if event.data else "?"
        self.status_label.setText(f"Task {task_id} completed!")
        self.state = ComponentState.ACTIVE
        self._logger.info(f"Task {task_id} completed")

    def on_task_failed(self, event: Event):
        error_msg = event.data.get("error", "Unknown error") if event.data else "Unknown error"
        task_id = event.data.get("task_id", "?") if event.data else "?"
        self.status_label.setText(f"Task {task_id} failed: {error_msg}")
        self.state = ComponentState.ERROR
        self._logger.error(f"Task {task_id} failed: {error_msg}")
        self.error_occurred.emit(error_msg, ErrorSeverity.ERROR)

    def on_task_cancelled(self, event: Event):
        task_id = event.data.get("task_id", "?") if event.data else "?"
        self.status_label.setText(f"Task {task_id} cancelled.")
        self.state = ComponentState.DEACTIVATED
        self._logger.info(f"Task {task_id} cancelled")

    async def initialize(self) -> bool:
        self.state = ComponentState.INITIALIZED
        return True

    async def activate(self) -> bool:
        self.state = ComponentState.ACTIVE
        return True

    async def deactivate(self) -> bool:
        self.state = ComponentState.DEACTIVATED
        return True 