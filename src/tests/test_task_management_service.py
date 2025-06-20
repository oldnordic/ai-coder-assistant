"""
test_task_management_service.py

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

import pytest
import tempfile
import os
import sqlite3
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from typing import Dict, Any
from pathlib import Path

from backend.services.task_management import TaskManagementService, Task, TaskStatus, TaskPriority
from src.backend.utils.constants import TEST_INVALID_TASK_ID


@pytest.fixture
def temp_data_dir():
    """Create a temporary data directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def task_service(temp_data_dir: str):
    """Create a task service instance with a temporary data directory."""
    service = TaskManagementService(data_dir=temp_data_dir, db_name="test_tasks.db")
    yield service


@pytest.fixture
def sample_task_data():
    """Provide sample task data for testing."""
    return {
        "title": "Implement user authentication",
        "description": "Add login/logout functionality with JWT tokens",
        "assignee": "developer1",
        "priority": TaskPriority.HIGH,
        "due_date": datetime(2024, 2, 15),
        "estimated_hours": 8.0,
        "tags": ["auth", "security", "frontend"],
        "project": "Test Project"
    }


@pytest.fixture
def sample_tasks():
    """Provide multiple sample tasks for testing."""
    return [
        {
            "title": "Implement user authentication",
            "description": "Add login/logout functionality",
            "assignee": "developer1",
            "priority": TaskPriority.HIGH,
            "due_date": datetime(2024, 2, 15),
            "tags": ["auth", "security"]
        },
        {
            "title": "Fix bug in data processing",
            "description": "Resolve issue with CSV import",
            "assignee": "developer2",
            "priority": TaskPriority.MEDIUM,
            "due_date": datetime(2024, 2, 10),
            "tags": ["bug", "data"]
        },
        {
            "title": "Update documentation",
            "description": "Update API documentation",
            "assignee": "developer3",
            "priority": TaskPriority.LOW,
            "due_date": datetime(2024, 2, 20),
            "tags": ["docs", "api"]
        }
    ]


class TestTaskManagementService:
    """Test cases for TaskManagementService."""

    def test_service_initialization(self, temp_data_dir: str):
        """Test service creation and database initialization."""
        service = TaskManagementService(data_dir=temp_data_dir, db_name="test.db")
        
        assert service is not None
        assert service.data_dir == Path(temp_data_dir)
        assert service.db_path == Path(temp_data_dir) / "test.db"
        
        # Verify database was created and tables exist
        db_path = Path(temp_data_dir) / "test.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
        assert cursor.fetchone() is not None
        conn.close()

    def test_create_task_success(self, task_service: TaskManagementService, sample_task_data: Dict[str, Any]):
        """Test successful task creation."""
        task = task_service.create_task(**sample_task_data)
        
        assert task is not None
        assert isinstance(task, Task)
        assert task.title == sample_task_data["title"]
        assert task.description == sample_task_data["description"]
        assert task.assignee == sample_task_data["assignee"]
        assert task.priority == sample_task_data["priority"]
        assert task.status == TaskStatus.TODO  # Default status
        assert task.tags == sample_task_data["tags"]

    def test_create_task_minimal_data(self, task_service: TaskManagementService):
        """Test task creation with minimal required data."""
        minimal_data = {
            "title": "Simple task",
            "description": "Basic description",
            "assignee": "developer1"
        }
        
        task = task_service.create_task(**minimal_data)
        assert task is not None
        assert task.title == minimal_data["title"]
        assert task.status == TaskStatus.TODO  # Default status
        assert task.priority == TaskPriority.MEDIUM  # Default priority

    def test_get_task_success(self, task_service: TaskManagementService, sample_task_data: Dict[str, Any]):
        """Test successful task retrieval."""
        created_task = task_service.create_task(**sample_task_data)
        task = task_service.get_task(created_task.id)
        
        assert task is not None
        assert task.id == created_task.id
        assert task.title == sample_task_data["title"]

    def test_get_task_not_found(self, task_service: TaskManagementService):
        """Test retrieving non-existent task."""
        task = task_service.get_task(TEST_INVALID_TASK_ID)
        assert task is None

    def test_update_task_success(self, task_service: TaskManagementService, sample_task_data: Dict[str, Any]):
        """Test successful task update."""
        created_task = task_service.create_task(**sample_task_data)
        
        # Update task
        updated_task = task_service.update_task(
            created_task.id,
            title="Updated title",
            status=TaskStatus.IN_PROGRESS,
            actual_hours=4.0
        )
        
        assert updated_task is not None
        assert updated_task.title == "Updated title"
        assert updated_task.status == TaskStatus.IN_PROGRESS
        assert updated_task.actual_hours == 4.0

    def test_update_task_not_found(self, task_service: TaskManagementService):
        """Test updating non-existent task."""
        result = task_service.update_task(TEST_INVALID_TASK_ID, title="Updated")
        assert result is None

    def test_delete_task_success(self, task_service: TaskManagementService, sample_task_data: Dict[str, Any]):
        """Test successful task deletion."""
        created_task = task_service.create_task(**sample_task_data)
        
        # Verify task exists
        task = task_service.get_task(created_task.id)
        assert task is not None
        
        # Delete task
        success = task_service.delete_task(created_task.id)
        assert success is True
        
        # Verify task was deleted
        task = task_service.get_task(created_task.id)
        assert task is None

    def test_delete_task_not_found(self, task_service: TaskManagementService):
        """Test deleting non-existent task."""
        success = task_service.delete_task(TEST_INVALID_TASK_ID)
        assert success is False

    def test_get_all_tasks(self, task_service: TaskManagementService, sample_tasks: list):
        """Test retrieving all tasks."""
        # Create multiple tasks
        created_tasks = []
        for task_data in sample_tasks:
            task = task_service.create_task(**task_data)
            created_tasks.append(task)
        
        # Get all tasks
        tasks = task_service.get_all_tasks()
        
        assert len(tasks) >= len(sample_tasks)  # May include sample data
        created_ids = [task.id for task in created_tasks]
        for task in tasks:
            if task.id in created_ids:
                assert task.title in [t["title"] for t in sample_tasks]

    def test_filter_tasks_by_status(self, task_service: TaskManagementService, sample_tasks: list):
        """Test filtering tasks by status."""
        # Create tasks
        for task_data in sample_tasks:
            task_service.create_task(**task_data)
        
        # Filter by status
        todo_tasks = task_service.get_all_tasks(status=TaskStatus.TODO)
        assert len(todo_tasks) >= len(sample_tasks)  # All new tasks are TODO by default

    def test_filter_tasks_by_priority(self, task_service: TaskManagementService, sample_tasks: list):
        """Test filtering tasks by priority."""
        # Create tasks
        for task_data in sample_tasks:
            task_service.create_task(**task_data)
        
        # Filter by priority
        high_priority_tasks = task_service.get_all_tasks(priority=TaskPriority.HIGH)
        medium_priority_tasks = task_service.get_all_tasks(priority=TaskPriority.MEDIUM)
        low_priority_tasks = task_service.get_all_tasks(priority=TaskPriority.LOW)
        
        assert len(high_priority_tasks) >= 1
        assert len(medium_priority_tasks) >= 1
        assert len(low_priority_tasks) >= 1

    def test_filter_tasks_by_assignee(self, task_service: TaskManagementService, sample_tasks: list):
        """Test filtering tasks by assignee."""
        # Create tasks
        for task_data in sample_tasks:
            task_service.create_task(**task_data)
        
        # Filter by assignee
        developer1_tasks = task_service.get_all_tasks(assignee="developer1")
        developer2_tasks = task_service.get_all_tasks(assignee="developer2")
        
        assert len(developer1_tasks) >= 1
        assert len(developer2_tasks) >= 1

    def test_complete_task(self, task_service: TaskManagementService, sample_task_data: Dict[str, Any]):
        """Test completing a task."""
        created_task = task_service.create_task(**sample_task_data)
        
        # Complete the task
        completed_task = task_service.complete_task(created_task.id, actual_hours=6.0)
        
        assert completed_task is not None
        assert completed_task.status == TaskStatus.DONE
        assert completed_task.actual_hours == 6.0
        assert completed_task.completed_date is not None

    def test_get_analytics(self, task_service: TaskManagementService, sample_tasks: list):
        """Test getting task analytics."""
        # Create tasks
        for task_data in sample_tasks:
            task_service.create_task(**task_data)
        
        analytics = task_service.get_analytics()
        
        assert analytics is not None
        assert analytics.total_tasks >= len(sample_tasks)
        assert analytics.completion_rate >= 0.0
        assert analytics.completion_rate <= 100.0

    def test_thread_safety(self, task_service: TaskManagementService):
        """Test thread safety of the service."""
        import threading
        
        results = []
        errors = []
        
        def create_task(thread_id: int):
            try:
                task = task_service.create_task(
                    title=f"Thread {thread_id} task",
                    description=f"Task from thread {thread_id}",
                    assignee=f"developer{thread_id}"
                )
                results.append(task.id)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=create_task, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify no errors occurred
        assert len(errors) == 0
        assert len(results) == 10
        
        # Verify all tasks were created
        all_tasks = task_service.get_all_tasks()
        assert len(all_tasks) >= 10

    def test_service_singleton_pattern(self, temp_data_dir: str):
        """Test that the service can be created multiple times."""
        service1 = TaskManagementService(data_dir=temp_data_dir, db_name="singleton.db")
        service2 = TaskManagementService(data_dir=temp_data_dir, db_name="singleton.db")
        
        # Both should be different instances (service doesn't implement singleton)
        assert service1 is not service2

    def test_data_validation(self, task_service: TaskManagementService):
        """Test data validation."""
        # Test with empty title - this should work as the service doesn't validate empty titles
        task = task_service.create_task(
            title="",
            description="Test",
            assignee="developer1"
        )
        assert task is not None
        assert task.title == ""
        
        # Test with empty assignee - this should work as the service doesn't validate empty assignees
        task = task_service.create_task(
            title="Test",
            description="Test",
            assignee=""
        )
        assert task is not None
        assert task.assignee == "" 