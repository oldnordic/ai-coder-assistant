"""Unit tests for the Model Manager service."""

import pytest
from unittest.mock import Mock, patch
from src.backend.services.model_manager import (
    ModelManager, ModelType, ModelState, BaseModel,
    OllamaModel, LocalModel, CloudModel
)
from src.core.events import Event, EventType

@pytest.fixture
def model_manager():
    """Create a fresh ModelManager instance for each test."""
    manager = ModelManager()
    manager._models.clear()  # Ensure clean state
    return manager

@pytest.mark.asyncio
async def test_singleton_pattern():
    """Test that ModelManager follows singleton pattern."""
    manager1 = ModelManager()
    manager2 = ModelManager()
    assert manager1 is manager2

@pytest.mark.asyncio
async def test_load_model(model_manager):
    """Test loading a model."""
    model_id = "test-model"
    
    # Test successful load
    with patch.object(OllamaModel, 'load', return_value=True):
        success = await model_manager.load_model(model_id, ModelType.OLLAMA)
        assert success
        assert model_id in model_manager._models
        assert model_manager._models[model_id].state == ModelState.LOADED

    # Test loading already loaded model
    with patch.object(OllamaModel, 'load', return_value=True):
        success = await model_manager.load_model(model_id, ModelType.OLLAMA)
        assert success  # Should succeed but not create new model

    # Test failed load
    another_model = "failed-model"
    with patch.object(OllamaModel, 'load', return_value=False):
        success = await model_manager.load_model(another_model, ModelType.OLLAMA)
        assert not success
        assert another_model not in model_manager._models

@pytest.mark.asyncio
async def test_unload_model(model_manager):
    """Test unloading a model."""
    model_id = "test-model"
    
    # First load a model
    with patch.object(OllamaModel, 'load', return_value=True):
        await model_manager.load_model(model_id, ModelType.OLLAMA)
    
    # Test successful unload
    with patch.object(OllamaModel, 'unload', return_value=True):
        success = await model_manager.unload_model(model_id)
        assert success
        assert model_id not in model_manager._models

    # Test unloading non-existent model
    success = await model_manager.unload_model("non-existent")
    assert success  # Should succeed as model doesn't exist

    # Test failed unload
    with patch.object(OllamaModel, 'load', return_value=True):
        await model_manager.load_model(model_id, ModelType.OLLAMA)
    
    with patch.object(OllamaModel, 'unload', return_value=False):
        success = await model_manager.unload_model(model_id)
        assert not success
        assert model_id in model_manager._models

@pytest.mark.asyncio
async def test_model_health_check(model_manager):
    """Test model health checks."""
    model_id = "test-model"
    
    # Test health check on non-existent model
    is_healthy = await model_manager.is_model_healthy(model_id)
    assert not is_healthy

    # Load model and test health check
    with patch.object(OllamaModel, 'load', return_value=True):
        await model_manager.load_model(model_id, ModelType.OLLAMA)
    
    with patch.object(OllamaModel, 'is_healthy', return_value=True):
        is_healthy = await model_manager.is_model_healthy(model_id)
        assert is_healthy

    with patch.object(OllamaModel, 'is_healthy', return_value=False):
        is_healthy = await model_manager.is_model_healthy(model_id)
        assert not is_healthy

@pytest.mark.asyncio
async def test_get_loaded_models(model_manager):
    """Test getting loaded models."""
    # Initially no models
    models = model_manager.get_loaded_models()
    assert len(models) == 0

    # Load some models
    model_ids = ["model1", "model2", "model3"]
    with patch.object(OllamaModel, 'load', return_value=True):
        for model_id in model_ids:
            await model_manager.load_model(model_id, ModelType.OLLAMA)
    
    models = model_manager.get_loaded_models()
    assert len(models) == 3
    for model_id in model_ids:
        assert model_id in models
        assert models[model_id] == ModelState.LOADED

@pytest.mark.asyncio
async def test_model_events(model_manager):
    """Test model-related events."""
    model_id = "test-model"
    events = []
    
    def event_handler(event: Event):
        events.append(event)
    
    model_manager.event_bus.subscribe(EventType.MODEL_LOADED, event_handler)
    model_manager.event_bus.subscribe(EventType.MODEL_UNLOADED, event_handler)
    model_manager.event_bus.subscribe(EventType.MODEL_ERROR, event_handler)

    # Test MODEL_LOADED event
    with patch.object(OllamaModel, 'load', return_value=True):
        await model_manager.load_model(model_id, ModelType.OLLAMA)
        assert len(events) == 1
        assert events[0].type == EventType.MODEL_LOADED
        assert events[0].data['model_id'] == model_id
        assert events[0].data['model_type'] == ModelType.OLLAMA.value

    # Test MODEL_UNLOADED event
    with patch.object(OllamaModel, 'unload', return_value=True):
        await model_manager.unload_model(model_id)
        assert len(events) == 2
        assert events[1].type == EventType.MODEL_UNLOADED
        assert events[1].data['model_id'] == model_id

    # Test MODEL_ERROR event
    with patch.object(OllamaModel, 'load', side_effect=Exception("Test error")):
        await model_manager.load_model(model_id, ModelType.OLLAMA)
        assert len(events) == 3
        assert events[2].type == EventType.MODEL_ERROR
        assert events[2].data['model_id'] == model_id
        assert "Test error" in events[2].data['error']

@pytest.mark.asyncio
async def test_different_model_types(model_manager):
    """Test loading different types of models."""
    models = [
        ("ollama-model", ModelType.OLLAMA, OllamaModel),
        ("local-model", ModelType.LOCAL, LocalModel),
        ("cloud-model", ModelType.CLOUD, CloudModel)
    ]
    
    for model_id, model_type, model_class in models:
        with patch.object(model_class, 'load', return_value=True):
            success = await model_manager.load_model(model_id, model_type)
            assert success
            assert model_id in model_manager._models
            assert isinstance(model_manager._models[model_id], model_class)

@pytest.mark.asyncio
async def test_config_change_handler(model_manager):
    """Test handling of configuration changes."""
    events = []
    
    def config_handler(event: Event):
        events.append(event)
    
    model_manager.event_bus.subscribe(EventType.CONFIG_CHANGED, config_handler)
    
    # Simulate config change event
    event = Event(
        type=EventType.CONFIG_CHANGED,
        data={'scanner.default_model': 'new-model'}
    )
    model_manager._handle_config_change(event)
    
    # Verify the event was handled
    assert len(events) == 1
    assert events[0].type == EventType.CONFIG_CHANGED
    assert 'scanner.default_model' in events[0].data