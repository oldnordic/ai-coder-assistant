"""Core module for AI Coder Assistant.

This module provides core functionality used across the application:
- Configuration management
- Logging
- Error handling
- Thread management
- Event system
"""

__version__ = '1.0.0'

from .config import Config
from .logging import LogManager
from .error import ErrorHandler
from .events import EventBus, Event, EventType

__all__ = ['Config', 'LogManager', 'ErrorHandler', 'EventBus', 'Event', 'EventType'] 