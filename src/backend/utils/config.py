"""
Centralized Configuration Management

This module provides a centralized configuration system for the AI Coder Assistant,
replacing hardcoded URLs and settings with configurable values.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
import json
import logging

logger = logging.getLogger(__name__)


class AppConfig:
    """Centralized application configuration manager."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self._config = self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get the default configuration file path."""
        project_root = Path(__file__).parent.parent.parent.parent
        return str(project_root / "config" / "app_config.json")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default."""
        default_config = {
            "urls": {
                "ollama_base": "http://localhost:11434",
                "ollama_api": "http://localhost:11434/api",
                "lm_studio_base": "http://localhost:1234/v1",
                "web_server_default_host": "localhost",
                "web_server_default_port": 8080,
                "api_server_default_port": 8000
            },
            "timeouts": {
                "http_short": 5,
                "http_long": 30,
                "scan": 300,
                "linter": 60,
                "ai_suggestion": 120
            },
            "limits": {
                "max_file_size_kb": 1024,
                "max_issues_per_file": 100,
                "max_code_context_length": 4000,
                "max_code_snippet_length": 500,
                "max_prompt_length": 8000,
                "max_suggestion_length": 1000,
                "max_description_length": 500,
                "max_error_message_length": 200,
                "max_depth_spinbox_value": 3,
                "max_pages_spinbox_value": 10
            },
            "ui": {
                "main_window_min_width": 1200,
                "main_window_min_height": 800,
                "progress_dialog_min_value": 0,
                "progress_dialog_max_value": 100,
                "log_output_max_height": 200,
                "doc_urls_input_max_height": 100,
                "status_box_min_height": 150
            },
            "scanning": {
                "default_scan_limit": 1000,
                "default_max_workers": 4,
                "bytes_per_kb": 1024
            }
        }
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    file_config = json.load(f)
                    # Merge with defaults, allowing file config to override
                    self._merge_configs(default_config, file_config)
                    logger.info(f"Configuration loaded from {self.config_path}")
            else:
                # Create default config file
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                with open(self.config_path, 'w') as f:
                    json.dump(default_config, f, indent=2)
                logger.info(f"Default configuration created at {self.config_path}")
        except Exception as e:
            logger.warning(f"Failed to load configuration from {self.config_path}: {e}")
            logger.info("Using default configuration")
        
        return default_config
    
    def _merge_configs(self, default: Dict[str, Any], override: Dict[str, Any]) -> None:
        """Recursively merge configuration dictionaries."""
        for key, value in override.items():
            if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                self._merge_configs(default[key], value)
            else:
                default[key] = value
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'urls.ollama_base')."""
        keys = key_path.split('.')
        value = self._config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any) -> None:
        """Set configuration value using dot notation."""
        keys = key_path.split('.')
        config = self._config
        
        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        # Set the value
        config[keys[-1]] = value
    
    def save(self) -> None:
        """Save current configuration to file."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self._config, f, indent=2)
            logger.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
    
    def reload(self) -> None:
        """Reload configuration from file."""
        self._config = self._load_config()


# Global configuration instance
_config_instance: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Get the global configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = AppConfig()
    return _config_instance


def get_url(key: str) -> str:
    """Get URL configuration value."""
    return get_config().get(f"urls.{key}", "")


def get_timeout(key: str) -> int:
    """Get timeout configuration value."""
    return get_config().get(f"timeouts.{key}", 30)


def get_limit(key: str) -> int:
    """Get limit configuration value."""
    return get_config().get(f"limits.{key}", 1000)


def get_ui_setting(key: str) -> Any:
    """Get UI configuration value."""
    return get_config().get(f"ui.{key}", None)


def get_scan_setting(key: str) -> Any:
    """Get scanning configuration value."""
    return get_config().get(f"scanning.{key}", None) 