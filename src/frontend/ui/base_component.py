"""Base UI component for AI Coder Assistant."""

from typing import Any, Callable, Dict, Optional, Set

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget

from core.config import Config
from core.error import ErrorHandler, ErrorSeverity
from core.events import Event, EventBus, EventType
from core.logging import LogManager


class BaseComponent(QWidget):
    """Base class for all UI components.

    Provides common functionality for UI components including:
    - Configuration management
    - Logging
    - Error handling
    - Event handling
    - State management
    """

    # Signals for UI updates
    error_occurred = pyqtSignal(str)  # Display error message
    status_changed = pyqtSignal(str)  # Update status bar
    progress_updated = pyqtSignal(int)  # Update progress bar

    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the component.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        # Initialize core services
        self.config = Config()
        self.logger = LogManager().get_logger(self.__class__.__name__)
        self.error_handler = ErrorHandler()
        self.event_bus = EventBus()

        # Initialize component state
        self._event_handlers: Dict[EventType, Set[Callable[[Event], None]]] = {}
        self._is_initialized = False
        self._is_active = False

        # Connect error signal
        self.error_occurred.connect(self._handle_error_signal)

    def initialize(self) -> None:
        """Initialize the component.

        This method should be called after the component is created and before
        it is shown. Subclasses should override this method to perform their
        own initialization, but should always call the parent implementation.
        """
        if self._is_initialized:
            return

        try:
            self._setup_ui()
            self._connect_signals()
            self._register_event_handlers()
            self._load_config()

            self._is_initialized = True
            self.logger.debug(f"{self.__class__.__name__} initialized")

        except Exception as e:
            self.handle_error(e, "initialize")

    def _setup_ui(self) -> None:
        """Set up the UI.

        Subclasses should override this method to create and arrange their
        widgets. The base implementation does nothing.
        """
        pass

    def _connect_signals(self) -> None:
        """Connect Qt signals and slots.

        Subclasses should override this method to connect their signals.
        The base implementation does nothing.
        """
        pass

    def _register_event_handlers(self) -> None:
        """Register event handlers.

        Subclasses should override this method to register their event
        handlers. The base implementation does nothing.
        """
        pass

    def _load_config(self) -> None:
        """Load component configuration.

        Subclasses should override this method to load their configuration.
        The base implementation does nothing.
        """
        pass

    def subscribe_to_event(
        self, event_type: EventType, handler: Callable[[Event], None]
    ) -> None:
        """Subscribe to an event type.

        Args:
            event_type: Type of event to subscribe to
            handler: Event handler function
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = set()

        self._event_handlers[event_type].add(handler)
        self.event_bus.subscribe(event_type, handler)

    def unsubscribe_from_event(
        self, event_type: EventType, handler: Callable[[Event], None]
    ) -> None:
        """Unsubscribe from an event type.

        Args:
            event_type: Type of event to unsubscribe from
            handler: Event handler function
        """
        if event_type in self._event_handlers:
            self._event_handlers[event_type].discard(handler)
            self.event_bus.unsubscribe(event_type, handler)

    def handle_error(
        self,
        error: Exception,
        function: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Handle an error.

        Args:
            error: The error that occurred
            function: Name of the function where the error occurred
            severity: Error severity
            details: Additional error details
        """
        response = self.error_handler.handle_error(
            error, self.__class__.__name__, function, severity, details
        )

        # Emit error signal for UI update
        self.error_occurred.emit(self.error_handler.create_user_message(response))

    def _handle_error_signal(self, message: str) -> None:
        """Handle error signal.

        Args:
            message: Error message to display
        """
        # Subclasses should override this to display the error message
        # in an appropriate way (e.g., message box, status bar, etc.)
        self.logger.error(f"UI Error: {message}")

    def update_status(self, message: str) -> None:
        """Update status message.

        Args:
            message: Status message to display
        """
        self.status_changed.emit(message)

    def update_progress(self, value: int) -> None:
        """Update progress value.

        Args:
            value: Progress value (0-100)
        """
        self.progress_updated.emit(max(0, min(value, 100)))

    def save_config(self) -> None:
        """Save component configuration.

        Subclasses should override this method to save their configuration.
        The base implementation does nothing.
        """
        pass

    def activate(self) -> None:
        """Activate the component.

        This method is called when the component becomes active (e.g., when
        its tab is selected). Subclasses should override this method to
        perform any necessary activation tasks.
        """
        self._is_active = True

    def deactivate(self) -> None:
        """Deactivate the component.

        This method is called when the component becomes inactive (e.g., when
        another tab is selected). Subclasses should override this method to
        perform any necessary deactivation tasks.
        """
        self._is_active = False

    def is_active(self) -> bool:
        """Check if the component is active.

        Returns:
            bool: True if the component is active
        """
        return self._is_active

    def cleanup(self) -> None:
        """Clean up the component.

        This method is called when the component is being destroyed.
        Subclasses should override this method to perform cleanup tasks,
        but should always call the parent implementation.
        """
        # Unsubscribe from all events
        for event_type, handlers in self._event_handlers.items():
            for handler in handlers:
                self.event_bus.unsubscribe(event_type, handler)

        # Save configuration
        self.save_config()

        self._is_initialized = False
        self._is_active = False
