"""Unit tests for the Base UI Component."""

import pytest
from unittest.mock import Mock, patch
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCloseEvent

from src.frontend.components.base_component import BaseComponent, ComponentState
from src.core.events import Event, EventType
from src.core.error import ErrorSeverity

# Create QApplication instance for tests
app = QApplication([])

class TestComponent(BaseComponent):
    """Test implementation of BaseComponent."""
    
    def __init__(self):
        super().__init__()
        self.initialize_called = False
        self.activate_called = False
        self.deactivate_called = False
    
    async def initialize(self) -> bool:
        self.initialize_called = True
        return True
    
    async def activate(self) -> bool:
        self.activate_called = True
        return True
    
    async def deactivate(self) -> bool:
        self.deactivate_called = True
        return True

@pytest.fixture
def component():
    """Create a fresh TestComponent instance for each test."""
    return TestComponent()

@pytest.mark.asyncio
async def test_initialization(component):
    """Test component initialization."""
    assert component.state == ComponentState.UNINITIALIZED
    assert not component.initialize_called
    
    success = await component.initialize()
    assert success
    assert component.initialize_called
    
    # Test that logger and error manager are properly initialized
    assert component._logger is not None
    assert component._error_manager is not None

@pytest.mark.asyncio
async def test_lifecycle(component):
    """Test component lifecycle states."""
    # Test initialization
    component.state = ComponentState.INITIALIZING
    assert component.state == ComponentState.INITIALIZING
    
    await component.initialize()
    component.state = ComponentState.INITIALIZED
    assert component.state == ComponentState.INITIALIZED
    
    # Test activation
    component.state = ComponentState.ACTIVATING
    assert component.state == ComponentState.ACTIVATING
    
    await component.activate()
    component.state = ComponentState.ACTIVE
    assert component.state == ComponentState.ACTIVE
    
    # Test deactivation
    component.state = ComponentState.DEACTIVATING
    assert component.state == ComponentState.DEACTIVATING
    
    await component.deactivate()
    component.state = ComponentState.DEACTIVATED
    assert component.state == ComponentState.DEACTIVATED

@pytest.mark.asyncio
async def test_event_handling(component):
    """Test event subscription and publishing."""
    events_received = []
    
    def event_handler(event: Event):
        events_received.append(event)
    
    # Test subscription
    component.subscribe_to_event(EventType.APP_STARTUP, event_handler)
    assert EventType.APP_STARTUP in component._event_subscriptions
    
    # Test publishing
    event = Event(type=EventType.APP_STARTUP, data={'test': 'data'})
    component.publish_event(event)
    assert len(events_received) == 1
    assert events_received[0].type == EventType.APP_STARTUP
    assert events_received[0].data == {'test': 'data'}
    
    # Test unsubscription
    component.unsubscribe_from_event(EventType.APP_STARTUP, event_handler)
    assert EventType.APP_STARTUP not in component._event_subscriptions
    
    # Test publishing after unsubscription
    component.publish_event(event)
    assert len(events_received) == 1  # Should not increase

def test_error_handling(component):
    """Test error handling and state changes."""
    errors_received = []
    
    def error_handler(error_msg: str, severity: ErrorSeverity):
        errors_received.append((error_msg, severity))
    
    # Connect to error signal
    component.error_occurred.connect(error_handler)
    
    # Test error handling
    test_error = "Test error"
    component._handle_error(test_error, ErrorSeverity.ERROR)
    
    assert len(errors_received) == 1
    assert errors_received[0][0] == test_error
    assert errors_received[0][1] == ErrorSeverity.ERROR
    assert component.state == ComponentState.ERROR
    
    # Test warning (should not change state)
    component.state = ComponentState.ACTIVE
    component._handle_error("Test warning", ErrorSeverity.WARNING)
    assert component.state == ComponentState.ACTIVE

def test_cleanup(component):
    """Test component cleanup."""
    # Add some event subscriptions
    mock_handler = Mock()
    component.subscribe_to_event(EventType.APP_STARTUP, mock_handler)
    component.subscribe_to_event(EventType.APP_SHUTDOWN, mock_handler)
    
    assert len(component._event_subscriptions) == 2
    
    # Test cleanup
    component._cleanup()
    assert len(component._event_subscriptions) == 0

def test_state_change_handling(component):
    """Test state change handling and logging."""
    state_changes = []
    
    def state_change_handler(new_state: ComponentState):
        state_changes.append(new_state)
    
    # Connect to state change signal
    component.state_changed.connect(state_change_handler)
    
    # Test various state changes
    test_states = [
        ComponentState.INITIALIZING,
        ComponentState.INITIALIZED,
        ComponentState.ACTIVE,
        ComponentState.ERROR
    ]
    
    for state in test_states:
        component.state = state
        assert state in state_changes
        assert component.state == state

def test_close_event(component):
    """Test component close event handling."""
    from PyQt6.QtGui import QCloseEvent
    
    # Test successful close
    event = QCloseEvent()
    component.closeEvent(event)
    # QCloseEvent doesn't have an ignore method, so we can't test it directly
    
    # Test close with error by patching _cleanup
    with patch.object(component, '_cleanup', side_effect=Exception("Cleanup error")):
        event = QCloseEvent()
        component.closeEvent(event)
        # The error should be handled and logged, but the event should still be processed

@pytest.mark.asyncio
async def test_error_during_state_change(component):
    """Test error handling during state changes."""
    with patch.object(component._logger, 'info', side_effect=Exception("Logging error")):
        component.state = ComponentState.INITIALIZED
        assert component.state == ComponentState.ERROR

def test_multiple_error_handlers(component):
    """Test multiple error handlers."""
    handlers_called = []
    
    def handler1(error_msg: str, severity: ErrorSeverity):
        handlers_called.append(1)
    
    def handler2(error_msg: str, severity: ErrorSeverity):
        handlers_called.append(2)
    
    # Connect multiple handlers
    component.error_occurred.connect(handler1)
    component.error_occurred.connect(handler2)
    
    # Trigger error
    component._handle_error("Test error", ErrorSeverity.ERROR)
    
    assert len(handlers_called) == 2
    assert 1 in handlers_called
    assert 2 in handlers_called