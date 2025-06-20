"""Event system for AI Coder Assistant."""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Callable, Dict, Optional, Set
from threading import Lock
from core.logging import LogManager

class EventType(Enum):
    """Built-in event types."""
    # Application events
    APP_STARTUP = auto()
    APP_SHUTDOWN = auto()
    CONFIG_CHANGED = auto()
    
    # UI events
    UI_READY = auto()
    UI_THEME_CHANGED = auto()
    
    # Task events
    TASK_STARTED = auto()
    TASK_COMPLETED = auto()
    TASK_FAILED = auto()
    TASK_CANCELLED = auto()
    
    # Scanner events
    SCAN_STARTED = auto()
    SCAN_PROGRESS = auto()
    SCAN_COMPLETED = auto()
    SCAN_FAILED = auto()
    
    # Model events
    MODEL_LOADED = auto()
    MODEL_UNLOADED = auto()
    MODEL_ERROR = auto()

@dataclass
class Event:
    """Event data container."""
    type: EventType
    data: Optional[Dict[str, Any]] = None
    source: Optional[str] = None

class EventBus:
    """Event management and distribution.
    
    Provides a centralized event system for inter-module communication.
    Uses a singleton pattern to ensure consistent event handling state.
    """
    
    _instance: Optional['EventBus'] = None
    _lock = Lock()
    
    def __new__(cls) -> 'EventBus':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self.logger = LogManager().get_logger('event_bus')
            self._handlers: Dict[EventType, Set[Callable[[Event], None]]] = {}
            self._initialized = True
    
    def subscribe(self, event_type: EventType, handler: Callable[[Event], None]) -> None:
        """Subscribe to an event type."""
        with self._lock:
            if event_type not in self._handlers:
                self._handlers[event_type] = set()
            self._handlers[event_type].add(handler)
            self.logger.debug(f"Subscribed handler to {event_type.name}")
    
    def unsubscribe(self, event_type: EventType, handler: Callable[[Event], None]) -> None:
        """Unsubscribe from an event type."""
        with self._lock:
            if event_type in self._handlers:
                self._handlers[event_type].discard(handler)
                if not self._handlers[event_type]:
                    del self._handlers[event_type]
                self.logger.debug(f"Unsubscribed handler from {event_type.name}")
    
    def publish(self, event: Event) -> None:
        """Publish an event to all subscribers."""
        handlers = self._handlers.get(event.type, set())
        
        if not handlers:
            self.logger.debug(f"No handlers for event {event.type.name}")
            return
        
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                self.logger.error(
                    f"Error in event handler for {event.type.name}: {str(e)}",
                    exc_info=True
                )
    
    def get_subscriber_count(self, event_type: EventType) -> int:
        """Get the number of subscribers for an event type."""
        return len(self._handlers.get(event_type, set()))
    
    def clear_all_subscribers(self) -> None:
        """Remove all event subscribers."""
        with self._lock:
            self._handlers.clear()
            self.logger.info("Cleared all event subscribers") 