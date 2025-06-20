"""Error handling for AI Coder Assistant."""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Dict, Optional
from core.logging import LogManager

class ErrorSeverity(Enum):
    """Error severity levels."""
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()

@dataclass
class ErrorContext:
    """Context information for errors."""
    module: str
    function: str
    details: Dict[str, Any]

@dataclass
class ErrorResponse:
    """Standardized error response."""
    error_type: str
    message: str
    severity: ErrorSeverity
    context: ErrorContext
    suggestion: Optional[str] = None

class ErrorHandler:
    """Centralized error handling.
    
    Provides consistent error handling, logging, and user feedback across the application.
    Uses a singleton pattern to ensure consistent error handling state.
    """
    
    _instance: Optional['ErrorHandler'] = None
    
    def __new__(cls) -> 'ErrorHandler':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.logger = LogManager().get_logger('error_handler')
    
    def handle_error(
        self,
        error: Exception,
        module: str,
        function: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        details: Optional[Dict[str, Any]] = None,
        suggestion: Optional[str] = None
    ) -> ErrorResponse:
        """Handle an error and return a standardized response."""
        context = ErrorContext(
            module=module,
            function=function,
            details=details or {}
        )
        
        response = ErrorResponse(
            error_type=error.__class__.__name__,
            message=str(error),
            severity=severity,
            context=context,
            suggestion=suggestion
        )
        
        self._log_error(response)
        return response
    
    def _log_error(self, response: ErrorResponse) -> None:
        """Log an error with appropriate severity."""
        log_message = (
            f"{response.error_type}: {response.message}\n"
            f"Module: {response.context.module}\n"
            f"Function: {response.context.function}\n"
            f"Details: {response.context.details}"
        )
        
        if response.suggestion:
            log_message += f"\nSuggestion: {response.suggestion}"
        
        if response.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
        elif response.severity == ErrorSeverity.ERROR:
            self.logger.error(log_message)
        elif response.severity == ErrorSeverity.WARNING:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
    
    def create_user_message(self, response: ErrorResponse) -> str:
        """Create a user-friendly error message."""
        message = f"An error occurred: {response.message}"
        
        if response.suggestion:
            message += f"\n\nSuggestion: {response.suggestion}"
        
        return message 