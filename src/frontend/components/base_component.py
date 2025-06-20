"""Base UI component for AI Coder Assistant."""

from enum import Enum, auto
from typing import Any, Optional, Set

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget

from core.error import ErrorHandler, ErrorSeverity
from core.events import Event, EventBus, EventType
from core.logging import LogManager


class ComponentState(Enum):
    """Component lifecycle states."""

    UNINITIALIZED = auto()
    INITIALIZING = auto()
    INITIALIZED = auto()
    ACTIVATING = auto()
    ACTIVE = auto()
    DEACTIVATING = auto()
    DEACTIVATED = auto()
    ERROR = auto()


class BaseComponent(QWidget):
    """Base class for all UI components.

    Provides:
    - Lifecycle management (initialize, activate, deactivate)
    - Event handling
    - Error management
    - State tracking
    """

    # Signals for state changes
    state_changed = pyqtSignal(ComponentState)
    error_occurred = pyqtSignal(str, ErrorSeverity)

    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the component."""
        super().__init__(parent)

        self._state = ComponentState.UNINITIALIZED
        self._event_bus = EventBus()
        self._error_manager = ErrorHandler()
        self._logger = LogManager().get_logger(self.__class__.__name__)
        self._event_subscriptions: Set[EventType] = set()

        # Connect signals
        self.state_changed.connect(self._handle_state_change)
        # Don't connect error_occurred to avoid infinite loop

    @property
    def state(self) -> ComponentState:
        """Get the current component state."""
        return self._state

    @state.setter
    def state(self, new_state: ComponentState) -> None:
        """Set the component state and emit state_changed signal."""
        if new_state != self._state:
            old_state = self._state
            self._state = new_state
            self.state_changed.emit(new_state)
            self._logger.debug(f"State changed from {old_state} to {new_state}")

    def subscribe_to_event(self, event_type: EventType, handler: callable) -> None:
        """Subscribe to an event type."""
        self._event_bus.subscribe(event_type, handler)
        self._event_subscriptions.add(event_type)
        self._logger.debug(f"Subscribed to event {event_type.name}")

    def unsubscribe_from_event(self, event_type: EventType, handler: callable) -> None:
        """Unsubscribe from an event type."""
        self._event_bus.unsubscribe(event_type, handler)
        self._event_subscriptions.discard(event_type)
        self._logger.debug(f"Unsubscribed from event {event_type.name}")

    def publish_event(self, event: Event) -> None:
        """Publish an event."""
        self._event_bus.publish(event)

    def _handle_state_change(self, new_state: ComponentState) -> None:
        """Handle component state changes."""
        try:
            if new_state == ComponentState.ERROR:
                self._logger.error("Component entered error state")
            elif new_state == ComponentState.INITIALIZED:
                self._logger.info("Component initialized")
            elif new_state == ComponentState.ACTIVE:
                self._logger.info("Component activated")
            elif new_state == ComponentState.DEACTIVATED:
                self._logger.info("Component deactivated")
        except Exception as e:
            self._logger.error(f"Error handling state change: {e}")
            self.handle_error(str(e), ErrorSeverity.ERROR)

    def handle_error(self, error_msg: str, severity: ErrorSeverity) -> None:
        """Public method to handle errors and emit signals."""
        try:
            # Create a generic exception for the error handler
            error = Exception(error_msg)
            self._error_manager.handle_error(
                error=error,
                module=self.__class__.__module__,
                function=self.__class__.__name__,
                severity=severity,
            )
            # Set error state for ERROR and CRITICAL severities
            if severity in [ErrorSeverity.ERROR, ErrorSeverity.CRITICAL]:
                self.state = ComponentState.ERROR
            # Emit the error signal for external handlers
            self.error_occurred.emit(error_msg, severity)
        except Exception as e:
            self._logger.error(f"Error handling error: {e}")
            # Still emit the original error signal
            self.error_occurred.emit(error_msg, severity)

    def _handle_error(self, error_msg: str, severity: ErrorSeverity) -> None:
        """Legacy method - now calls the public handle_error method."""
        self.handle_error(error_msg, severity)

    def _cleanup(self) -> None:
        """Clean up resources and event subscriptions."""
        try:
            # Unsubscribe from all events
            for event_type in self._event_subscriptions.copy():
                self._event_bus.unsubscribe(event_type, None)
            self._event_subscriptions.clear()

            # Additional cleanup
            self._logger.info("Component cleanup completed")
        except Exception as e:
            self._logger.error(f"Error during cleanup: {e}")
            self.handle_error(str(e), ErrorSeverity.ERROR)

    async def initialize(self) -> bool:
        """Initialize the component.

        This method should be overridden by subclasses to perform
        any necessary initialization.

        Returns:
            bool: True if initialization was successful, False otherwise.
        """
        raise NotImplementedError("Subclasses must implement initialize()")

    async def activate(self) -> bool:
        """Activate the component.

        This method should be overridden by subclasses to perform
        any necessary activation steps.

        Returns:
            bool: True if activation was successful, False otherwise.
        """
        raise NotImplementedError("Subclasses must implement activate()")

    async def deactivate(self) -> bool:
        """Deactivate the component.

        This method should be overridden by subclasses to perform
        any necessary deactivation steps.

        Returns:
            bool: True if deactivation was successful, False otherwise.
        """
        raise NotImplementedError("Subclasses must implement deactivate()")

    def closeEvent(self, event: Any) -> None:
        """Handle component close event."""
        try:
            self._cleanup()
            super().closeEvent(event)
        except Exception as e:
            self._logger.error(f"Error during close: {e}")
            self.handle_error(str(e), ErrorSeverity.ERROR)
            event.ignore()
