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
    
    @property
    def app_config_dir(self) -> Path:
        """Get the application configuration directory path (relative to project root)."""
        # Get the project root directory (assuming this is run from the project root)
        project_root = Path(__file__).parent.parent.parent.parent
        return project_root / 'config'
    
    def get_config_file_path(self, config_name: str) -> Path:
        """Get the path to a specific configuration file.
        
        Args:
            config_name: Name of the configuration file (e.g., 'llm_studio_config.json')
            
        Returns:
            Path to the configuration file
        """
        return self.app_config_dir / config_name
    
    def load_config_file(self, config_name: str) -> Dict[str, Any]:
        """Load a specific configuration file.
        
        Args:
            config_name: Name of the configuration file to load
            
        Returns:
            Configuration data as dictionary
            
        Raises:
            FileNotFoundError: If the configuration file doesn't exist
            json.JSONDecodeError: If the configuration file is invalid JSON
        """
        config_path = self.get_config_file_path(config_name)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def save_config_file(self, config_name: str, config_data: Dict[str, Any]) -> None:
        """Save data to a specific configuration file.
        
        Args:
            config_name: Name of the configuration file to save
            config_data: Configuration data to save
        """
        config_path = self.get_config_file_path(config_name)
        
        # Ensure the config directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=4)
    
    def config_file_exists(self, config_name: str) -> bool:
        """Check if a configuration file exists.
        
        Args:
            config_name: Name of the configuration file to check
            
        Returns:
            True if the file exists, False otherwise
        """
        return self.get_config_file_path(config_name).exists()
    
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
            },
            'config_files': {
                'llm_studio': 'llm_studio_config.json',
                'security': 'security_config.json',
                'pr_automation': 'pr_automation_config.json',
                'security_intelligence': 'security_intelligence_config.json',
                'code_standards': 'code_standards_config.json'
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