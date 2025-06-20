"""Logging management for AI Coder Assistant."""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional
from src.core.config import Config

class LogManager:
    """Centralized logging management.
    
    Provides consistent logging configuration and access across the application.
    Uses a singleton pattern to ensure consistent logging state.
    """
    
    _instance: Optional['LogManager'] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'LogManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._config = Config()
            self._setup_logging()
            self._initialized = True
    
    @property
    def log_dir(self) -> Path:
        """Get the log directory path."""
        return Path(self._config.get('app.log_dir', 'logs'))
    
    def _setup_logging(self) -> None:
        """Set up logging configuration."""
        # Create log directory if it doesn't exist
        if not self.log_dir.exists():
            self.log_dir.mkdir(parents=True)
        
        # Get log level from config
        log_level = getattr(logging, self._config.get('app.log_level', 'INFO'))
        
        # Configure root logger
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Create file handlers
        self._setup_file_handlers()
        
        # Create logger for this module
        self.logger = logging.getLogger('ai_coder_assistant')
        self.logger.setLevel(log_level)
    
    def _setup_file_handlers(self) -> None:
        """Set up file handlers for different log levels."""
        handlers = {
            'error': (logging.ERROR, 'error.log'),
            'info': (logging.INFO, 'info.log'),
            'debug': (logging.DEBUG, 'debug.log')
        }
        
        for name, (level, filename) in handlers.items():
            handler = logging.handlers.RotatingFileHandler(
                self.log_dir / filename,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
            handler.setLevel(level)
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            logging.getLogger('').addHandler(handler)
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger instance for a specific module."""
        return logging.getLogger(f'ai_coder_assistant.{name}')
    
    def set_level(self, level: str) -> None:
        """Set the logging level."""
        numeric_level = getattr(logging, level.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError(f'Invalid log level: {level}')
        
        logging.getLogger('').setLevel(numeric_level)
        self._config.set('app.log_level', level)
    
    def cleanup(self) -> None:
        """Clean up old log files."""
        try:
            for handler in logging.getLogger('').handlers[:]:
                handler.close()
                logging.getLogger('').removeHandler(handler)
        except Exception as e:
            print(f"Error cleaning up logs: {e}") 