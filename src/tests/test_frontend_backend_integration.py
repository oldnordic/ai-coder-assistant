"""Integration tests for frontend-backend interaction."""

import pytest
import tempfile
import shutil
import asyncio
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from unittest.mock import Mock, patch

from src.frontend.components.scanner_component import ScannerComponent
from src.frontend.components.model_management_component import ModelManagementComponent
from src.frontend.components.task_management_component import TaskManagementComponent
from src.frontend.components.base_component import ComponentState
from src.backend.services.model_manager import ModelManager, ModelType
from src.backend.services.task_management import TaskManagementService
from src.core.events import Event, EventBus, EventType
from src.core.error import ErrorSeverity

app = QApplication([])

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture
def event_bus():
    """Create a shared event bus for testing."""
    return EventBus()

@pytest.fixture
def model_manager():
    """Create a ModelManager instance for testing."""
    return ModelManager()

@pytest.fixture
def task_service(temp_data_dir):
    """Create a TaskManagementService instance for testing."""
    service = TaskManagementService(str(temp_data_dir), "test_tasks.db")
    yield service
    if hasattr(service, 'connection_pool'):
        service.connection_pool.close_all()

@pytest.fixture
def scanner_component(event_bus):
    """Create a ScannerComponent instance for testing."""
    return ScannerComponent()

@pytest.fixture
def model_component(event_bus):
    """Create a ModelManagementComponent instance for testing."""
    return ModelManagementComponent()

@pytest.fixture
def task_component(event_bus):
    """Create a TaskManagementComponent instance for testing."""
    return TaskManagementComponent()

class TestFrontendBackendIntegration:
    """Integration tests for frontend-backend interaction."""

    def test_event_flow_scanner_to_backend(self, scanner_component, event_bus):
        """Test event flow from scanner UI to backend services."""
        events_received = []
        
        def event_handler(event: Event):
            events_received.append(event)
        
        # Subscribe to scan events
        event_bus.subscribe(EventType.SCAN_STARTED, event_handler)
        event_bus.subscribe(EventType.SCAN_PROGRESS, event_handler)
        event_bus.subscribe(EventType.SCAN_COMPLETED, event_handler)
        
        # Trigger scan from UI
        scanner_component.start_scan()
        
        # Verify events were published
        assert len(events_received) >= 1
        assert events_received[0].type == EventType.SCAN_STARTED
        assert events_received[0].data["source"] == "ui"

    def test_event_flow_model_management(self, model_component, event_bus):
        """Test event flow for model management."""
        events_received = []
        
        def event_handler(event: Event):
            events_received.append(event)
        
        # Subscribe to model events
        event_bus.subscribe(EventType.MODEL_LOADING, event_handler)
        event_bus.subscribe(EventType.MODEL_LOADED, event_handler)
        event_bus.subscribe(EventType.MODEL_ERROR, event_handler)
        
        # Trigger model loading from UI
        model_component.load_model()
        
        # Verify events were published
        assert len(events_received) >= 1
        assert events_received[0].type == EventType.MODEL_LOADING
        assert "model_id" in events_received[0].data

    def test_event_flow_task_management(self, task_component, event_bus):
        """Test event flow for task management."""
        events_received = []
        
        def event_handler(event: Event):
            events_received.append(event)
        
        # Subscribe to task events
        event_bus.subscribe(EventType.TASK_STARTED, event_handler)
        event_bus.subscribe(EventType.TASK_COMPLETED, event_handler)
        event_bus.subscribe(EventType.TASK_FAILED, event_handler)
        
        # Trigger task creation from UI
        task_component.create_task()
        
        # Verify events were published
        assert len(events_received) >= 1
        assert events_received[0].type == EventType.TASK_STARTED
        assert events_received[0].data["action"] == "create"

    def test_error_propagation_across_layers(self, scanner_component, event_bus):
        """Test error propagation from backend to frontend."""
        errors_received = []
        
        def error_handler(error_msg: str, severity: ErrorSeverity):
            errors_received.append((error_msg, severity))
        
        scanner_component.error_occurred.connect(error_handler)
        
        # Simulate backend error
        error_event = Event(
            type=EventType.SCAN_FAILED,
            data={"error": "Backend scan error", "source": "backend"}
        )
        event_bus.publish(error_event)
        
        # Verify error was handled by frontend
        assert len(errors_received) >= 1
        assert errors_received[0][0] == "Backend scan error"
        assert errors_received[0][1] == ErrorSeverity.ERROR

    def test_component_lifecycle_integration(self, scanner_component, model_component, task_component):
        """Test component lifecycle integration."""
        components = [scanner_component, model_component, task_component]
        
        # Test initialization
        for component in components:
            assert component.state == ComponentState.UNINITIALIZED
        
        # Test activation
        for component in components:
            component.state = ComponentState.ACTIVE
            assert component.state == ComponentState.ACTIVE
        
        # Test deactivation
        for component in components:
            component.state = ComponentState.DEACTIVATED
            assert component.state == ComponentState.DEACTIVATED

    def test_concurrent_event_handling(self, scanner_component, model_component, task_component, event_bus):
        """Test concurrent event handling across multiple components."""
        events_processed = []
        
        def track_event(event: Event):
            events_processed.append(event.type)
        
        # Subscribe all components to track events
        for component in [scanner_component, model_component, task_component]:
            event_bus.subscribe(EventType.APP_STARTUP, track_event)
        
        # Publish multiple events concurrently
        events = [
            Event(type=EventType.APP_STARTUP, data={"source": "test"}),
            Event(type=EventType.SCAN_STARTED, data={"source": "test"}),
            Event(type=EventType.MODEL_LOADING, data={"model_id": "test"}),
            Event(type=EventType.TASK_STARTED, data={"action": "test"})
        ]
        
        for event in events:
            event_bus.publish(event)
        
        # Verify events were processed
        assert len(events_processed) >= 3  # At least APP_STARTUP events

    @pytest.mark.asyncio
    async def test_async_operations_integration(self, model_manager, task_service):
        """Test async operations integration between services."""
        # Test model loading
        success = await model_manager.load_model("test-model", ModelType.OLLAMA)
        assert isinstance(success, bool)
        
        # Test task creation and scheduling
        task = task_service.create_task(
            title="Integration Test Task",
            description="Test task for integration",
            assignee="Test User",
            priority=task_service.TaskPriority.MEDIUM
        )
        assert task is not None
        assert task.title == "Integration Test Task"

    def test_data_persistence_integration(self, task_service, temp_data_dir):
        """Test data persistence integration."""
        # Create a task
        task = task_service.create_task(
            title="Persistence Test Task",
            description="Test task for persistence",
            assignee="Test User",
            priority=task_service.TaskPriority.HIGH
        )
        
        # Verify task was persisted
        retrieved_task = task_service.get_task(task.id)
        assert retrieved_task is not None
        assert retrieved_task.title == "Persistence Test Task"
        assert retrieved_task.priority == task_service.TaskPriority.HIGH
        
        # Test task updates
        updated_task = task_service.update_task(
            task.id,
            status=task_service.TaskStatus.IN_PROGRESS,
            description="Updated description"
        )
        assert updated_task is not None
        assert updated_task.status == task_service.TaskStatus.IN_PROGRESS

    def test_error_recovery_integration(self, scanner_component, model_component, task_component):
        """Test error recovery integration across components."""
        # Simulate error states
        scanner_component.state = ComponentState.ERROR
        model_component.state = ComponentState.ERROR
        task_component.state = ComponentState.ERROR
        
        # Verify error states
        assert scanner_component.state == ComponentState.ERROR
        assert model_component.state == ComponentState.ERROR
        assert task_component.state == ComponentState.ERROR
        
        # Test recovery
        scanner_component.state = ComponentState.ACTIVE
        model_component.state = ComponentState.ACTIVE
        task_component.state = ComponentState.ACTIVE
        
        assert scanner_component.state == ComponentState.ACTIVE
        assert model_component.state == ComponentState.ACTIVE
        assert task_component.state == ComponentState.ACTIVE

class TestPerformanceIntegration:
    """Performance integration tests."""

    def test_event_throughput(self, event_bus):
        """Test event throughput across the system."""
        events_processed = 0
        
        def event_counter(event: Event):
            nonlocal events_processed
            events_processed += 1
        
        # Subscribe to multiple event types
        for event_type in [EventType.SCAN_STARTED, EventType.MODEL_LOADING, EventType.TASK_STARTED]:
            event_bus.subscribe(event_type, event_counter)
        
        # Publish many events
        for i in range(100):
            event = Event(type=EventType.SCAN_STARTED, data={"id": i})
            event_bus.publish(event)
        
        # Verify all events were processed
        assert events_processed == 100

    def test_concurrent_component_operations(self, scanner_component, model_component, task_component):
        """Test concurrent operations across components."""
        import threading
        import time
        
        results = []
        
        def component_operation(component, operation_id):
            component.state = ComponentState.ACTIVE
            time.sleep(0.01)  # Simulate work
            results.append(operation_id)
        
        # Run operations concurrently
        threads = []
        for i in range(10):
            component = [scanner_component, model_component, task_component][i % 3]
            thread = threading.Thread(target=component_operation, args=(component, i))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify all operations completed
        assert len(results) == 10
        assert set(results) == set(range(10)) 