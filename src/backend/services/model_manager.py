"""Model management service for AI Coder Assistant."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Optional, Type, List, Any
from datetime import datetime
from core.events import Event, EventBus, EventType
from core.config import Config
from core.logging import LogManager
from backend.services.ollama_client import OllamaClient
from backend.services.model_persistence import ModelPersistenceService, ModelConfig, ModelStateRecord, ModelType as PersistenceModelType, ModelState as PersistenceModelState

class ModelType(Enum):
    """Supported model types."""
    OLLAMA = "ollama"
    LOCAL = "local"
    CLOUD = "cloud"

class ModelState(Enum):
    """Model states."""
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    ERROR = "error"

class BaseModel(ABC):
    """Base class for all model implementations."""
    
    def __init__(self, model_id: str):
        self.model_id = model_id
        self.state = ModelState.UNLOADED
        self.logger = LogManager().get_logger(f"model.{model_id}")
    
    @abstractmethod
    async def load(self) -> bool:
        """Load the model."""
        pass
    
    @abstractmethod
    async def unload(self) -> bool:
        """Unload the model."""
        pass
    
    @abstractmethod
    async def is_healthy(self) -> bool:
        """Check if the model is healthy and responsive."""
        pass

class OllamaModel(BaseModel):
    """Ollama model implementation."""
    
    def __init__(self, model_id: str):
        super().__init__(model_id)
        self.client = OllamaClient()
        self.loaded = False

    async def load(self) -> bool:
        try:
            self.state = ModelState.LOADING
            # Check if model is available
            models = await self.client.list_models()
            if self.model_id not in models:
                self.logger.error(f"Ollama model '{self.model_id}' not found.")
                self.state = ModelState.ERROR
                return False
            self.state = ModelState.LOADED
            self.loaded = True
            return True
        except Exception as e:
            self.logger.error(f"Failed to load Ollama model: {e}")
            self.state = ModelState.ERROR
            return False
    
    async def unload(self) -> bool:
        try:
            self.state = ModelState.UNLOADED
            self.loaded = False
            await self.client.close()
            return True
        except Exception as e:
            self.logger.error(f"Failed to unload Ollama model: {e}")
            return False
    
    async def is_healthy(self) -> bool:
        try:
            if not self.loaded:
                return False
            models = await self.client.list_models()
            return self.model_id in models
        except Exception:
            return False

class LocalModel(BaseModel):
    """Local model implementation (stub for future integration)."""
    async def load(self) -> bool:
        # TODO: Implement local model loading logic
        self.state = ModelState.LOADED
        return True
    async def unload(self) -> bool:
        self.state = ModelState.UNLOADED
        return True
    async def is_healthy(self) -> bool:
        return self.state == ModelState.LOADED

class CloudModel(BaseModel):
    """Cloud model implementation (stub for future integration)."""
    async def load(self) -> bool:
        # TODO: Implement cloud model loading logic
        self.state = ModelState.LOADED
        return True
    async def unload(self) -> bool:
        self.state = ModelState.UNLOADED
        return True
    async def is_healthy(self) -> bool:
        return self.state == ModelState.LOADED

class ModelManager:
    """Model management service.
    
    Handles loading, unloading, and managing different types of models.
    Uses event system for status updates and configuration changes.
    Integrates with persistence service for data storage.
    """
    
    _instance: Optional['ModelManager'] = None
    _model_types: Dict[ModelType, Type[BaseModel]] = {
        ModelType.OLLAMA: OllamaModel,
        ModelType.LOCAL: LocalModel,
        ModelType.CLOUD: CloudModel
    }
    
    def __new__(cls) -> 'ModelManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self.config = Config()
            self.event_bus = EventBus()
            self.logger = LogManager().get_logger('model_manager')
            self._models: Dict[str, BaseModel] = {}
            
            # Initialize persistence service
            self.persistence = ModelPersistenceService()
            
            self._setup_event_handlers()
            self._initialized = True
    
    def _setup_event_handlers(self) -> None:
        """Set up event handlers."""
        self.event_bus.subscribe(EventType.CONFIG_CHANGED, self._handle_config_change)
    
    def _handle_config_change(self, event: Event) -> None:
        """Handle configuration changes."""
        if event.data and 'scanner.default_model' in event.data:
            self.logger.info("Default model configuration changed")
    
    def _convert_model_type(self, model_type: ModelType) -> PersistenceModelType:
        """Convert internal model type to persistence model type."""
        return PersistenceModelType(model_type.value)
    
    def _convert_model_state(self, model_state: ModelState) -> PersistenceModelState:
        """Convert internal model state to persistence model state."""
        return PersistenceModelState(model_state.value)
    
    async def load_model(self, model_id: str, model_type: ModelType, 
                        name: Optional[str] = None, version: str = "1.0.0", 
                        description: Optional[str] = None, parameters: Optional[Dict[str, Any]] = None) -> bool:
        """Load a model of the specified type with persistence."""
        try:
            if model_id in self._models:
                self.logger.warning(f"Model {model_id} already exists")
                return True
            
            # Create or update model configuration in persistence
            config = ModelConfig(
                model_id=model_id,
                model_type=self._convert_model_type(model_type),
                name=name or model_id,
                version=version,
                description=description,
                parameters=parameters or {},
                updated_at=datetime.now()
            )
            
            # Save configuration
            if not self.persistence.save_model_config(config):
                self.logger.error(f"Failed to save model configuration for {model_id}")
                return False
            
            # Save loading state
            loading_state = ModelStateRecord(
                model_id=model_id,
                state=self._convert_model_state(ModelState.LOADING),
                timestamp=datetime.now()
            )
            self.persistence.save_model_state(loading_state)
            
            model_class = self._model_types.get(model_type)
            if not model_class:
                self.logger.error(f"Unsupported model type: {model_type}")
                return False
            
            model = model_class(model_id)
            success = await model.load()
            
            if success:
                self._models[model_id] = model
                
                # Save loaded state
                loaded_state = ModelStateRecord(
                    model_id=model_id,
                    state=self._convert_model_state(ModelState.LOADED),
                    timestamp=datetime.now(),
                    performance_metrics={"load_time": datetime.now().isoformat()}
                )
                self.persistence.save_model_state(loaded_state)
                
                self.event_bus.publish(Event(
                    type=EventType.MODEL_LOADED,
                    data={'model_id': model_id, 'model_type': model_type.value}
                ))
            else:
                # Save error state
                error_state = ModelStateRecord(
                    model_id=model_id,
                    state=self._convert_model_state(ModelState.ERROR),
                    timestamp=datetime.now(),
                    error_message="Failed to load model"
                )
                self.persistence.save_model_state(error_state)
            
            return success
        except Exception as e:
            self.logger.error(f"Failed to load model {model_id}: {e}")
            
            # Save error state
            error_state = ModelStateRecord(
                model_id=model_id,
                state=self._convert_model_state(ModelState.ERROR),
                timestamp=datetime.now(),
                error_message=str(e)
            )
            self.persistence.save_model_state(error_state)
            
            self.event_bus.publish(Event(
                type=EventType.MODEL_ERROR,
                data={'model_id': model_id, 'error': str(e)}
            ))
            return False
    
    async def unload_model(self, model_id: str) -> bool:
        """Unload a model with persistence."""
        try:
            model = self._models.get(model_id)
            if not model:
                self.logger.warning(f"Model {model_id} not found")
                return True
            
            success = await model.unload()
            if success:
                del self._models[model_id]
                
                # Save unloaded state
                unloaded_state = ModelStateRecord(
                    model_id=model_id,
                    state=self._convert_model_state(ModelState.UNLOADED),
                    timestamp=datetime.now()
                )
                self.persistence.save_model_state(unloaded_state)
                
                self.event_bus.publish(Event(
                    type=EventType.MODEL_UNLOADED,
                    data={'model_id': model_id}
                ))
            
            return success
        except Exception as e:
            self.logger.error(f"Failed to unload model {model_id}: {e}")
            return False
    
    async def get_model(self, model_id: str) -> Optional[BaseModel]:
        """Get a loaded model."""
        return self._models.get(model_id)
    
    async def is_model_healthy(self, model_id: str) -> bool:
        """Check if a model is healthy."""
        model = self._models.get(model_id)
        if not model:
            return False
        return await model.is_healthy()
    
    def get_loaded_models(self) -> Dict[str, ModelState]:
        """Get all loaded models and their states."""
        return {model_id: model.state for model_id, model in self._models.items()}
    
    def get_model_config(self, model_id: str) -> Optional[ModelConfig]:
        """Get model configuration from persistence."""
        return self.persistence.get_model_config(model_id)
    
    def get_all_model_configs(self, model_type: Optional[ModelType] = None) -> List[ModelConfig]:
        """Get all model configurations from persistence."""
        persistence_type = self._convert_model_type(model_type) if model_type else None
        return self.persistence.get_all_model_configs(persistence_type)
    
    def get_model_states(self, model_id: str, limit: int = 100) -> List[ModelStateRecord]:
        """Get model state history from persistence."""
        return self.persistence.get_model_states(model_id, limit)
    
    async def delete_model_config(self, model_id: str) -> bool:
        """Delete model configuration and unload if loaded."""
        try:
            # Unload model if it's currently loaded
            if model_id in self._models:
                await self.unload_model(model_id)
            
            # Delete from persistence
            return self.persistence.delete_model_config(model_id)
        except Exception as e:
            self.logger.error(f"Failed to delete model config {model_id}: {e}")
            return False
    
    def get_model_analytics(self) -> Dict[str, Any]:
        """Get model analytics from persistence."""
        return self.persistence.get_model_analytics()