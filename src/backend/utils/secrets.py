"""
secrets.py

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

Copyright (C) 2024 AI Coder Assistant Contributors
"""

"""
Secure Secrets Management Module

This module provides a secure way to handle API keys and other sensitive
configuration data using:
1. Environment variables (highest priority)
2. OS keychain via keyring (for persistent storage)
3. .env files (for local development)
4. Fallback to empty strings (for unconfigured services)
"""

import os
import logging
from typing import Optional, Dict, List
from pathlib import Path

# Check for dotenv availability
try:
    from dotenv import load_dotenv
    _dotenv_available = True
except ImportError:
    _dotenv_available = False
    load_dotenv = None
    logging.warning("python-dotenv not available. .env files will not be loaded.")

# Check for keyring availability
try:
    import keyring
    _keyring_available = True
except ImportError:
    _keyring_available = False
    keyring = None
    logging.warning("keyring not available. OS keychain will not be used.")

logger = logging.getLogger(__name__)


class SecretsManager:
    """
    Secure secrets management for API keys and sensitive configuration.
    
    This class provides a centralized way to manage secrets using:
    1. Environment variables (highest priority)
    2. OS keychain via keyring (for persistent storage)
    3. .env files (for local development)
    4. Fallback to empty strings (for unconfigured services)
    """
    
    def __init__(self, env_file_path: Optional[str] = None, service_name: str = "ai_coder_assistant"):
        """
        Initialize the secrets manager.
        
        Args:
            env_file_path: Optional path to .env file. If None, will look for .env in project root.
            service_name: Service name for keyring storage
        """
        self._secrets_cache: Dict[str, str] = {}
        self.service_name = service_name
        self._load_env_file(env_file_path)
    
    def _load_env_file(self, env_file_path: Optional[str] = None):
        """Load environment variables from .env file."""
        if not _dotenv_available or load_dotenv is None:
            logger.warning("python-dotenv not available. Skipping .env file loading.")
            return
            
        if env_file_path is None:
            # Look for .env file in project root
            project_root = Path(__file__).parent.parent.parent.parent
            env_file_path = str(project_root / ".env")
        
        if Path(env_file_path).exists():
            load_dotenv(env_file_path)
            logger.info(f"Loaded environment variables from {env_file_path}")
        else:
            logger.debug(f"No .env file found at {env_file_path}")
    
    def get_secret(self, key: str, default: str = "") -> str:
        """
        Retrieve a secret from environment variables or keyring.
        
        Priority order:
        1. Environment variables (highest priority)
        2. OS keychain via keyring
        3. Default value
        
        Args:
            key: The secret key name
            default: Default value if not found
            
        Returns:
            The secret value or default
        """
        # Check cache first
        if key in self._secrets_cache:
            return self._secrets_cache[key]
        
        # First, try environment variables
        value = os.environ.get(key)
        if value:
            self._secrets_cache[key] = value
            return value
        
        # Then, try keyring
        if _keyring_available and keyring:
            try:
                value = keyring.get_password(self.service_name, key)
                if value:
                    self._secrets_cache[key] = value
                    return value
            except Exception as e:
                logger.warning(f"Failed to retrieve {key} from keyring: {e}")
        
        # Return default
        self._secrets_cache[key] = default
        return default
    
    def save_secret(self, key: str, value: str, persist_to_keyring: bool = True) -> bool:
        """
        Save a secret to environment variables and optionally to keyring.
        
        Args:
            key: The secret key name
            value: The secret value to save
            persist_to_keyring: Whether to also save to OS keychain
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Set in environment for current session
            os.environ[key] = value
            
            # Update cache
            self._secrets_cache[key] = value
            
            # Optionally save to keyring for persistence
            if persist_to_keyring and _keyring_available and keyring:
                try:
                    keyring.set_password(self.service_name, key, value)
                    logger.info(f"Secret {key} saved to keyring successfully")
                except Exception as e:
                    logger.warning(f"Failed to save {key} to keyring: {e}")
            
            logger.info(f"Secret {key} saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error saving secret {key}: {e}")
            return False
    
    def delete_secret(self, key: str, remove_from_keyring: bool = True) -> bool:
        """
        Delete a secret from environment and optionally from keyring.
        
        Args:
            key: The secret key name
            remove_from_keyring: Whether to also remove from OS keychain
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Remove from environment
            if key in os.environ:
                del os.environ[key]
            
            # Remove from cache
            if key in self._secrets_cache:
                del self._secrets_cache[key]
            
            # Optionally remove from keyring
            if remove_from_keyring and _keyring_available and keyring:
                try:
                    keyring.delete_password(self.service_name, key)
                    logger.info(f"Secret {key} removed from keyring successfully")
                except Exception as e:
                    logger.warning(f"Failed to remove {key} from keyring: {e}")
            
            logger.info(f"Secret {key} deleted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting secret {key}: {e}")
            return False
    
    def load_secret(self, key: str) -> Optional[str]:
        """
        Load a secret from environment variables or keyring.
        
        Args:
            key: The secret key name
            
        Returns:
            The secret value or None if not found
        """
        try:
            value = self.get_secret(key)
            return value if value else None
            
        except Exception as e:
            logger.error(f"Error loading secret {key}: {e}")
            return None
    
    def get_api_key(self, provider: str) -> str:
        """
        Get API key for a specific provider.
        
        Args:
            provider: Provider name (e.g., 'openai', 'anthropic', 'google')
            
        Returns:
            API key for the provider
        """
        key_mapping = {
            'openai': 'OPENAI_API_KEY',
            'anthropic': 'ANTHROPIC_API_KEY',
            'claude': 'ANTHROPIC_API_KEY',  # Claude uses Anthropic API
            'google': 'GOOGLE_API_KEY',
            'google_gemini': 'GOOGLE_API_KEY',
            'azure': 'AZURE_API_KEY',
            'aws': 'AWS_ACCESS_KEY',
            'aws_secret': 'AWS_SECRET_KEY',
            'cohere': 'COHERE_API_KEY',
            'jira': 'JIRA_API_TOKEN',
            'servicenow': 'SERVICENOW_API_TOKEN',
        }
        
        env_key = key_mapping.get(provider.lower())
        if not env_key:
            logger.warning(f"Unknown provider: {provider}")
            return ""
        
        return self.get_secret(env_key)
    
    def get_service_config(self, service: str) -> Dict[str, str]:
        """
        Get configuration for a service (e.g., JIRA, ServiceNow).
        
        Args:
            service: Service name
            
        Returns:
            Dictionary of configuration values
        """
        configs = {
            'jira': {
                'base_url': self.get_secret('JIRA_BASE_URL'),
                'username': self.get_secret('JIRA_USERNAME'),
                'api_token': self.get_secret('JIRA_API_TOKEN'),
                'project_key': self.get_secret('JIRA_PROJECT_KEY'),
            },
            'servicenow': {
                'base_url': self.get_secret('SERVICENOW_BASE_URL'),
                'username': self.get_secret('SERVICENOW_USERNAME'),
                'api_token': self.get_secret('SERVICENOW_API_TOKEN'),
            },
        }
        
        return configs.get(service.lower(), {})
    
    def is_provider_configured(self, provider: str) -> bool:
        """
        Check if a provider is properly configured with API key.
        
        Args:
            provider: Provider name
            
        Returns:
            True if provider has API key configured
        """
        api_key = self.get_api_key(provider)
        return bool(api_key.strip())
    
    def is_service_configured(self, service: str) -> bool:
        """
        Check if a service is properly configured.
        
        Args:
            service: Service name
            
        Returns:
            True if service has required configuration
        """
        config = self.get_service_config(service)
        
        if service.lower() == 'jira':
            required_keys = ['base_url', 'username', 'api_token', 'project_key']
        elif service.lower() == 'servicenow':
            required_keys = ['base_url', 'username', 'api_token']
        else:
            return False
        
        return all(bool(config.get(key, '').strip()) for key in required_keys)
    
    def list_configured_providers(self) -> List[str]:
        """
        List all providers that have API keys configured.
        
        Returns:
            List of configured provider names
        """
        providers = ['openai', 'anthropic', 'google', 'azure', 'aws', 'cohere']
        return [p for p in providers if self.is_provider_configured(p)]
    
    def list_configured_services(self) -> List[str]:
        """
        List all services that are properly configured.
        
        Returns:
            List of configured service names
        """
        services = ['jira', 'servicenow']
        return [s for s in services if self.is_service_configured(s)]
    
    def clear_cache(self):
        """Clear the secrets cache."""
        self._secrets_cache.clear()
    
    def reload(self):
        """Reload secrets from environment (useful after .env file changes)."""
        self.clear_cache()
        self._load_env_file()


# Global instance
_secrets_manager = None


def get_secrets_manager() -> SecretsManager:
    """Get the global secrets manager instance."""
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = SecretsManager()
    return _secrets_manager


def get_secret(key: str, default: str = "") -> str:
    """
    Convenience function to get a secret.
    
    Args:
        key: Environment variable name
        default: Default value if not found
        
    Returns:
        The secret value
    """
    return get_secrets_manager().get_secret(key, default)


def get_api_key(provider: str) -> str:
    """
    Convenience function to get an API key.
    
    Args:
        provider: Provider name
        
    Returns:
        API key for the provider
    """
    return get_secrets_manager().get_api_key(provider)


def is_provider_configured(provider: str) -> bool:
    """
    Convenience function to check if a provider is configured.
    
    Args:
        provider: Provider name
        
    Returns:
        True if provider is configured
    """
    return get_secrets_manager().is_provider_configured(provider)


def is_service_configured(service: str) -> bool:
    """
    Convenience function to check if a service is configured.
    
    Args:
        service: Service name
        
    Returns:
        True if service is configured
    """
    return get_secrets_manager().is_service_configured(service)


# Pre-defined API key constants for backward compatibility
OPENAI_API_KEY = get_secret("OPENAI_API_KEY")
ANTHROPIC_API_KEY = get_secret("ANTHROPIC_API_KEY")
GOOGLE_API_KEY = get_secret("GOOGLE_API_KEY")
AZURE_API_KEY = get_secret("AZURE_API_KEY")
AWS_ACCESS_KEY = get_secret("AWS_ACCESS_KEY")
AWS_SECRET_KEY = get_secret("AWS_SECRET_KEY")
COHERE_API_KEY = get_secret("COHERE_API_KEY")
JIRA_API_TOKEN = get_secret("JIRA_API_TOKEN")
SERVICENOW_API_TOKEN = get_secret("SERVICENOW_API_TOKEN") 