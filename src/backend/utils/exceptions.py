"""
Custom Exception Classes for AI Coder Assistant

This module provides specific exception classes to replace generic exception handling
and improve error reporting and debugging.
"""

from typing import Optional, Any, Dict


class AICoderAssistantError(Exception):
    """Base exception class for AI Coder Assistant."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}: {self.message}"


class ConfigurationError(AICoderAssistantError):
    """Raised when there's an issue with configuration."""
    pass


class NetworkError(AICoderAssistantError):
    """Raised when there's a network-related error."""
    
    def __init__(self, message: str, url: Optional[str] = None, status_code: Optional[int] = None):
        details = {}
        if url:
            details["url"] = url
        if status_code:
            details["status_code"] = status_code
        super().__init__(message, details)


class AuthenticationError(AICoderAssistantError):
    """Raised when authentication fails."""
    pass


class ModelError(AICoderAssistantError):
    """Raised when there's an issue with AI models."""
    
    def __init__(self, message: str, model_name: Optional[str] = None, provider: Optional[str] = None):
        details = {}
        if model_name:
            details["model_name"] = model_name
        if provider:
            details["provider"] = provider
        super().__init__(message, details)


class LearningError(AICoderAssistantError):
    """Raised when there's an issue with the learning mechanism."""
    
    def __init__(self, message: str, learning_component: Optional[str] = None, data_type: Optional[str] = None):
        details = {}
        if learning_component:
            details["learning_component"] = learning_component
        if data_type:
            details["data_type"] = data_type
        super().__init__(message, details)


class DockerError(AICoderAssistantError):
    """Raised when there's an issue with Docker operations."""
    
    def __init__(self, message: str, container_id: Optional[str] = None, image_name: Optional[str] = None):
        details = {}
        if container_id:
            details["container_id"] = container_id
        if image_name:
            details["image_name"] = image_name
        super().__init__(message, details)


class TestError(AICoderAssistantError):
    """Raised when there's an issue with testing operations."""
    
    def __init__(self, message: str, test_type: Optional[str] = None, test_file: Optional[str] = None):
        details = {}
        if test_type:
            details["test_type"] = test_type
        if test_file:
            details["test_file"] = test_file
        super().__init__(message, details)


class RemediationError(AICoderAssistantError):
    """Raised when there's an issue with remediation operations."""
    
    def __init__(self, message: str, workspace_path: Optional[str] = None, issue_type: Optional[str] = None):
        details = {}
        if workspace_path:
            details["workspace_path"] = workspace_path
        if issue_type:
            details["issue_type"] = issue_type
        super().__init__(message, details)


class FileOperationError(AICoderAssistantError):
    """Raised when there's an issue with file operations."""
    
    def __init__(self, message: str, file_path: Optional[str] = None, operation: Optional[str] = None):
        details = {}
        if file_path:
            details["file_path"] = file_path
        if operation:
            details["operation"] = operation
        super().__init__(message, details)


class WebScrapingError(AICoderAssistantError):
    """Raised when web scraping fails."""
    
    def __init__(self, message: str, url: Optional[str] = None, status_code: Optional[int] = None):
        details = {}
        if url:
            details["url"] = url
        if status_code:
            details["status_code"] = status_code
        super().__init__(message, details)


class ScanningError(AICoderAssistantError):
    """Raised when code scanning fails."""
    
    def __init__(self, message: str, file_path: Optional[str] = None, linter: Optional[str] = None):
        details = {}
        if file_path:
            details["file_path"] = file_path
        if linter:
            details["linter"] = linter
        super().__init__(message, details)


class DatabaseError(AICoderAssistantError):
    """Raised when there's a database operation error."""
    pass


class ValidationError(AICoderAssistantError):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None):
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = value
        super().__init__(message, details)


class TimeoutError(AICoderAssistantError):
    """Raised when an operation times out."""
    
    def __init__(self, message: str, timeout_seconds: Optional[float] = None, operation: Optional[str] = None):
        details = {}
        if timeout_seconds:
            details["timeout_seconds"] = timeout_seconds
        if operation:
            details["operation"] = operation
        super().__init__(message, details)


class ResourceError(AICoderAssistantError):
    """Raised when there's an issue with system resources."""
    
    def __init__(self, message: str, resource_type: Optional[str] = None, resource_name: Optional[str] = None):
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_name:
            details["resource_name"] = resource_name
        super().__init__(message, details)


def handle_exception(func):
    """Decorator to handle exceptions and convert them to specific types."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AICoderAssistantError:
            # Re-raise our custom exceptions as-is
            raise
        except FileNotFoundError as e:
            raise FileOperationError(f"File not found: {e}", file_path=str(e))
        except PermissionError as e:
            raise FileOperationError(f"Permission denied: {e}", file_path=str(e))
        except ConnectionError as e:
            raise NetworkError(f"Connection error: {e}")
        except TimeoutError as e:
            raise TimeoutError(f"Operation timed out: {e}")
        except ValueError as e:
            raise ValidationError(f"Invalid value: {e}")
        except KeyError as e:
            raise ValidationError(f"Missing required field: {e}")
        except Exception as e:
            # Log the original exception for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
            raise AICoderAssistantError(f"Unexpected error: {e}")
    return wrapper 