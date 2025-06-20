"""Configuration management for AI Coder Assistant."""

from pathlib import Path
from typing import Any, Dict, Optional
import json
import os

class Config:
    """Configuration management class.
    
    Handles loading, saving, and accessing configuration settings across the application.
    Uses a singleton pattern to ensure consistent configuration state.
    """
    
    _instance: Optional['Config'] = None
    _config: Dict[str, Any] = {}
    
    def __new__(cls) -> 'Config':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._config:
            self.load_config()
    
    @property
    def config_dir(self) -> Path:
        """Get the configuration directory path."""
        return Path(os.path.expanduser('~/.ai_coder_assistant'))
    
    @property
    def config_file(self) -> Path:
        """Get the main configuration file path."""
        return self.config_dir / 'config.json'
    
    def load_config(self) -> None:
        """Load configuration from file."""
        try:
            if not self.config_dir.exists():
                self.config_dir.mkdir(parents=True)
            
            if not self.config_file.exists():
                self._create_default_config()
            
            with open(self.config_file, 'r') as f:
                self._config = json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            self._create_default_config()
    
    def save_config(self) -> None:
        """Save current configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self._config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def _create_default_config(self) -> None:
        """Create default configuration."""
        self._config = {
            'app': {
                'max_threads': 4,
                'log_level': 'INFO',
                'backup_enabled': True,
                'backup_dir': str(self.config_dir / 'backups')
            },
            'ui': {
                'theme': 'system',
                'font_size': 12,
                'show_line_numbers': True
            },
            'scanner': {
                'default_model': 'ollama',
                'excluded_dirs': ['.git', '__pycache__', 'node_modules'],
                'file_extensions': ['.py', '.js', '.ts', '.java', '.cpp', '.h']
            }
        }
        self.save_config()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        try:
            current = self._config
            for part in key.split('.'):
                current = current[part]
            return current
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value by key."""
        parts = key.split('.')
        current = self._config
        
        # Navigate to the correct nested level
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        # Set the value
        current[parts[-1]] = value
        self.save_config()
    
    def reset(self) -> None:
        """Reset configuration to defaults."""
        self._create_default_config()
        self.save_config() 