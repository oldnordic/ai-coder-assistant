"""Unit tests for ModelManagementComponent UI."""


import pytest
from PyQt6.QtWidgets import QApplication

from src.core.error import ErrorSeverity
from src.core.events import Event, EventType
from src.frontend.components.base_component import ComponentState
from src.frontend.components.model_management_component import ModelManagementComponent

app = QApplication([])


@pytest.fixture
def model_management_component():
    return ModelManagementComponent()


def test_initial_state(model_management_component):
    assert model_management_component.state == ComponentState.UNINITIALIZED
    assert model_management_component.status_label.text() == "No model loaded."
    assert model_management_component.current_model is None


def test_load_model(model_management_component):
    events = []
    model_management_component.publish_event = lambda event: events.append(event)
    model_management_component.model_selector.setCurrentText("ollama")
    model_management_component.load_model()
    assert "Loading model" in model_management_component.status_label.text()
    assert model_management_component.state == ComponentState.ACTIVATING
    assert len(events) == 1
    assert events[0].type == EventType.MODEL_LOADING
    assert events[0].data["model_id"] == "ollama"


def test_unload_model(model_management_component):
    events = []
    model_management_component.publish_event = lambda event: events.append(event)
    model_management_component.model_selector.setCurrentText("local")
    model_management_component.unload_model()
    assert "Unloading model" in model_management_component.status_label.text()
    assert model_management_component.state == ComponentState.ACTIVATING
    assert len(events) == 1
    assert events[0].type == EventType.MODEL_UNLOADED
    assert events[0].data["model_id"] == "local"


def test_on_model_loading(model_management_component):
    event = Event(type=EventType.MODEL_LOADING, data={"model_id": "cloud"})
    model_management_component.on_model_loading(event)
    assert "Loading model: cloud" in model_management_component.status_label.text()
    assert model_management_component.state == ComponentState.ACTIVATING


def test_on_model_loaded(model_management_component):
    event = Event(type=EventType.MODEL_LOADED, data={"model_id": "ollama"})
    model_management_component.on_model_loaded(event)
    assert "Model loaded: ollama" in model_management_component.status_label.text()
    assert model_management_component.state == ComponentState.ACTIVE
    assert model_management_component.current_model == "ollama"


def test_on_model_unloaded(model_management_component):
    event = Event(type=EventType.MODEL_UNLOADED, data={"model_id": "local"})
    model_management_component.on_model_unloaded(event)
    assert "Model unloaded: local" in model_management_component.status_label.text()
    assert model_management_component.state == ComponentState.DEACTIVATED
    assert model_management_component.current_model is None


def test_on_model_error(model_management_component):
    errors = []
    model_management_component.error_occurred.connect(
        lambda msg, sev: errors.append((msg, sev)))
    event = Event(
        type=EventType.MODEL_ERROR,
        data={
            "model_id": "cloud",
            "error": "Test error"})
    model_management_component.on_model_error(event)
    assert "Model error (cloud): Test error" in model_management_component.status_label.text()
    assert model_management_component.state == ComponentState.ERROR
    assert errors
    assert errors[0][0] == "Test error"
    assert errors[0][1] == ErrorSeverity.ERROR


@pytest.mark.asyncio
async def test_lifecycle_methods(model_management_component):
    assert await model_management_component.initialize() is True
    assert model_management_component.state == ComponentState.INITIALIZED
    assert await model_management_component.activate() is True
    assert model_management_component.state == ComponentState.ACTIVE
    assert await model_management_component.deactivate() is True
    assert model_management_component.state == ComponentState.DEACTIVATED
