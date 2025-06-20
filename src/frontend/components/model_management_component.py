"""Model Management UI component for AI Coder Assistant."""

from typing import Optional

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from core.error import ErrorSeverity
from core.events import Event, EventType
from core.logging import LogManager
from frontend.components.base_component import BaseComponent, ComponentState


class ModelManagementComponent(BaseComponent):
    """UI component for managing AI models (load/unload/status)."""

    def __init__(self, parent: Optional[object] = None):
        super().__init__(parent)
        self._logger = LogManager().get_logger("ModelManagementComponent")
        self._setup_ui()
        self.subscribe_to_event(EventType.MODEL_LOADED, self.on_model_loaded)
        self.subscribe_to_event(EventType.MODEL_UNLOADED, self.on_model_unloaded)
        self.subscribe_to_event(EventType.MODEL_ERROR, self.on_model_error)
        self.subscribe_to_event(EventType.MODEL_LOADING, self.on_model_loading)
        self.current_model = None

    def _setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.status_label = QLabel("No model loaded.")
        self.model_selector = QComboBox()
        self.model_selector.addItems(["ollama", "local", "cloud"])  # Example models
        self.load_button = QPushButton("Load Model")
        self.unload_button = QPushButton("Unload Model")
        self.load_button.clicked.connect(self.load_model)
        self.unload_button.clicked.connect(self.unload_model)
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.load_button)
        button_layout.addWidget(self.unload_button)
        self.layout.addWidget(QLabel("Select Model:"))
        self.layout.addWidget(self.model_selector)
        self.layout.addLayout(button_layout)
        self.layout.addWidget(self.status_label)
        self.setLayout(self.layout)

    @pyqtSlot()
    def load_model(self):
        model_id = self.model_selector.currentText()
        self.status_label.setText(f"Loading model: {model_id}...")
        self.state = ComponentState.ACTIVATING
        self.publish_event(
            Event(type=EventType.MODEL_LOADING, data={"model_id": model_id})
        )

    @pyqtSlot()
    def unload_model(self):
        model_id = self.model_selector.currentText()
        self.status_label.setText(f"Unloading model: {model_id}...")
        self.state = ComponentState.ACTIVATING
        self.publish_event(
            Event(type=EventType.MODEL_UNLOADED, data={"model_id": model_id})
        )

    def on_model_loading(self, event: Event):
        model_id = event.data.get("model_id", "?") if event.data else "?"
        self.status_label.setText(f"Loading model: {model_id}...")
        self.state = ComponentState.ACTIVATING
        self._logger.info(f"Loading model: {model_id}")

    def on_model_loaded(self, event: Event):
        model_id = event.data.get("model_id", "?") if event.data else "?"
        self.status_label.setText(f"Model loaded: {model_id}")
        self.state = ComponentState.ACTIVE
        self.current_model = model_id
        self._logger.info(f"Model loaded: {model_id}")

    def on_model_unloaded(self, event: Event):
        model_id = event.data.get("model_id", "?") if event.data else "?"
        self.status_label.setText(f"Model unloaded: {model_id}")
        self.state = ComponentState.DEACTIVATED
        self.current_model = None
        self._logger.info(f"Model unloaded: {model_id}")

    def on_model_error(self, event: Event):
        error_msg = (
            event.data.get("error", "Unknown error") if event.data else "Unknown error"
        )
        model_id = event.data.get("model_id", "?") if event.data else "?"
        self.status_label.setText(f"Model error ({model_id}): {error_msg}")
        self.state = ComponentState.ERROR
        self._logger.error(f"Model error ({model_id}): {error_msg}")
        self.error_occurred.emit(error_msg, ErrorSeverity.ERROR)

    async def initialize(self) -> bool:
        self.state = ComponentState.INITIALIZED
        return True

    async def activate(self) -> bool:
        self.state = ComponentState.ACTIVE
        return True

    async def deactivate(self) -> bool:
        self.state = ComponentState.DEACTIVATED
        return True
