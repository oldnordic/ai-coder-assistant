"""Unit tests for TaskManagementComponent UI."""


import pytest
from PyQt6.QtWidgets import QApplication

from src.backend.utils.constants import (
    TEST_TASK_ID_123,
    TEST_TASK_ID_456,
    TEST_TASK_ID_789,
)
from src.core.error import ErrorSeverity
from src.core.events import Event, EventType
from src.frontend.components.base_component import ComponentState
from src.frontend.components.task_management_component import TaskManagementComponent

app = QApplication([])


@pytest.fixture
def task_management_component():
    return TaskManagementComponent()


def test_initial_state(task_management_component):
    assert task_management_component.state == ComponentState.UNINITIALIZED
    assert task_management_component.status_label.text() == "Task Management Ready."
    assert task_management_component.tasks == []


def test_create_task(task_management_component):
    events = []
    task_management_component.publish_event = lambda event: events.append(event)
    task_management_component.create_task()
    assert "Creating task" in task_management_component.status_label.text()
    assert task_management_component.state == ComponentState.ACTIVATING
    assert len(events) == 1
    assert events[0].type == EventType.TASK_STARTED
    assert events[0].data["action"] == "create"


def test_schedule_tasks(task_management_component):
    events = []
    task_management_component.publish_event = lambda event: events.append(event)
    task_management_component.schedule_tasks()
    assert "Scheduling tasks" in task_management_component.status_label.text()
    assert task_management_component.state == ComponentState.ACTIVATING
    assert len(events) == 1
    assert events[0].type == EventType.TASK_STARTED
    assert events[0].data["action"] == "schedule"


def test_on_task_started(task_management_component):
    event = Event(type=EventType.TASK_STARTED, data={"action": "create"})
    task_management_component.on_task_started(event)
    assert "Task create started" in task_management_component.status_label.text()
    assert task_management_component.state == ComponentState.ACTIVATING


def test_on_task_completed(task_management_component):
    event = Event(type=EventType.TASK_COMPLETED, data={"task_id": TEST_TASK_ID_123})
    task_management_component.on_task_completed(event)
    assert f"Task {TEST_TASK_ID_123} completed!" in task_management_component.status_label.text()
    assert task_management_component.state == ComponentState.ACTIVE


def test_on_task_failed(task_management_component):
    errors = []
    task_management_component.error_occurred.connect(
        lambda msg, sev: errors.append((msg, sev)))
    event = Event(
        type=EventType.TASK_FAILED,
        data={
            "task_id": TEST_TASK_ID_456,
            "error": "Test error"})
    task_management_component.on_task_failed(event)
    assert f"Task {TEST_TASK_ID_456} failed: Test error" in task_management_component.status_label.text()
    assert task_management_component.state == ComponentState.ERROR
    assert errors
    assert errors[0][0] == "Test error"
    assert errors[0][1] == ErrorSeverity.ERROR


def test_on_task_cancelled(task_management_component):
    event = Event(type=EventType.TASK_CANCELLED, data={"task_id": TEST_TASK_ID_789})
    task_management_component.on_task_cancelled(event)
    assert f"Task {TEST_TASK_ID_789} cancelled." in task_management_component.status_label.text()
    assert task_management_component.state == ComponentState.DEACTIVATED


@pytest.mark.asyncio
async def test_lifecycle_methods(task_management_component):
    assert await task_management_component.initialize() is True
    assert task_management_component.state == ComponentState.INITIALIZED
    assert await task_management_component.activate() is True
    assert task_management_component.state == ComponentState.ACTIVE
    assert await task_management_component.deactivate() is True
    assert task_management_component.state == ComponentState.DEACTIVATED
