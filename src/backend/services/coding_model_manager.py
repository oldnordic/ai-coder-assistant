"""Coding Model Manager"""

import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class CodingModelManager:
    """Manages coding-specific AI models and their configurations."""
    
    def __init__(self):
        """Initialize the coding model manager."""
        self.models = {}
        self.active_model = None
        logger.info("Coding model manager initialized")
    
    def add_model(self, model_name: str, model_config: Dict[str, Any]) -> bool:
        """Add a new coding model."""
        try:
            self.models[model_name] = model_config
            logger.info(f"Added model: {model_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to add model {model_name}: {e}")
            return False
    
    def get_model(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get model configuration."""
        return self.models.get(model_name)
    
    def list_models(self) -> List[str]:
        """List all available models."""
        return list(self.models.keys())
    
    def set_active_model(self, model_name: str) -> bool:
        """Set the active model."""
        if model_name in self.models:
            self.active_model = model_name
            logger.info(f"Set active model: {model_name}")
            return True
        return False
    
    def get_active_model(self) -> Optional[str]:
        """Get the active model name."""
        return self.active_model
