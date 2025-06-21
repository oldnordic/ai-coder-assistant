"""
main_window.py

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

import concurrent.futures
import logging

# src/frontend/ui/main_window.py
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import QMutex, QMutexLocker, Qt, QTimer, QUrl, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QTableWidgetItem,
)

from src.backend.services import (
    acquire,
    ai_tools,
    get_available_models_sync,
    preprocess,
    scanner,
    trainer,
)
from src.backend.services.docker_utils import run_build_and_test_in_docker
from src.backend.services.llm_manager import LLMManager
from src.backend.services.scanner import ScanStatus, TaskStatus
from src.backend.utils import settings
from src.backend.utils.constants import (
    AI_SUGGESTION_TIMEOUT_SECONDS,
    BYTES_PER_KB,
    DEFAULT_MAX_DEPTH_SPINBOX_VALUE,
    DEFAULT_MAX_PAGES_SPINBOX_VALUE,
    DEFAULT_SCAN_LIMIT,
    DOC_URLS_INPUT_MAX_HEIGHT,
    LINTER_TIMEOUT_SECONDS,
    LOG_OUTPUT_MAX_HEIGHT,
    LOG_QUEUE_PROCESS_INTERVAL_MS,
    MAIN_WINDOW_MIN_HEIGHT,
    MAIN_WINDOW_MIN_WIDTH,
    MAX_CODE_CONTEXT_LENGTH,
    MAX_CODE_SNIPPET_LENGTH,
    MAX_DEPTH_SPINBOX_RANGE,
    MAX_DESCRIPTION_LENGTH,
    MAX_ERROR_MESSAGE_LENGTH,
    MAX_FILE_SIZE_KB,
    MAX_ISSUES_PER_FILE,
    MAX_PAGES_SPINBOX_RANGE,
    MAX_PROMPT_LENGTH,
    MAX_SUGGESTION_LENGTH,
    PROGRESS_DIALOG_MAX_VALUE,
    PROGRESS_DIALOG_MIN_VALUE,
    SCAN_TIMEOUT_SECONDS,
)
from src.backend.utils.settings import is_docker_available
from src.frontend.controllers.backend_controller import BackendController
from src.frontend.ui.ai_tab_widgets import setup_ai_tab
from src.frontend.ui.advanced_analytics_tab import AdvancedAnalyticsTab
from src.frontend.ui.cloud_models_tab import CloudModelsTab
from src.frontend.ui.code_standards_tab import CodeStandardsTab
from src.frontend.ui.collaboration_tab import CollaborationTab
from src.frontend.ui.continuous_learning_tab import ContinuousLearningTab
from src.frontend.ui.data_tab_widgets import setup_data_tab
from src.frontend.ui.markdown_viewer import MarkdownViewerDialog
from src.frontend.ui.model_manager_tab import ModelManagerTab
from src.frontend.ui.ollama_export_tab import OllamaExportTab, setup_ollama_export_tab
from src.frontend.ui.performance_optimization_tab import PerformanceOptimizationTab
from src.frontend.ui.pr_tab_widgets import setup_pr_tab
from src.frontend.ui.refactoring_tab import RefactoringTab
from src.frontend.ui.security_intelligence_tab import SecurityIntelligenceTab
from src.frontend.ui.settings_tab import SettingsTab
from src.frontend.ui.web_server_tab import WebServerTab

# Set up a logger for this module
logger = logging.getLogger(__name__)


class AICoderAssistant(QMainWindow):
    # --- Signals for thread-safe UI updates ---
    scan_progress_updated = pyqtSignal(int, int, str)
    scan_completed = pyqtSignal(list)
    # ---

    def __init__(self):
        super().__init__()

        # Initialize backend controller
        self.backend_controller = BackendController()
        self.scanner_service = self.backend_controller.get_scanner_service()

        # Initialize state variables
        self.scan_results = []
        self.current_suggestion_index = 0
        self.suggestion_list = []
        self.current_model_ref = None
        self.scan_directory = ""
        self.progress_dialog = None
        self.current_worker_id = None
        self.current_scan_future = None
        self.active_workers = []
        self.current_tokenizer_ref = None
        self.report_progress_dialog = None
        
        # Add flag to prevent multiple directory dialogs
        self._directory_dialog_open = False
        self._scan_in_progress = False

        # Initialize thread pool executor
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Initialize thread-safe logging
        self._log_mutex = QMutex()
        self._log_queue = []
        self._log_timer = QTimer()
        self._log_timer.timeout.connect(self._process_log_queue)
        self._log_timer.start(LOG_QUEUE_PROCESS_INTERVAL_MS)

        # Setup UI first to ensure GUI appears
        self.setup_ui()
        self.setup_menu()
        self.setup_ai_tab()
        self.setup_data_tab()
        self.setup_pr_tab()
        self.setup_cloud_models_tab()
        self.setup_model_manager_tab()
        self.setup_ollama_export_tab()
        self.setup_continuous_learning_tab()
        self.setup_code_standards_tab()
        self.setup_security_intelligence_tab()
        self.setup_settings_tab()
        self.setup_performance_optimization_tab()
        self.setup_advanced_analytics_tab()
        self.setup_web_server_tab()
        self.setup_collaboration_tab()

        # Connect all UI signals after setup is complete
        self._connect_signals()

        # Connect signals to their slots for thread-safe UI updates
        self.scan_progress_updated.connect(self._update_scan_progress_safe)
        self.scan_completed.connect(self._handle_scan_complete_ui)

        # Populate Ollama models
        self.populate_ollama_models()

        self.log_message("Main Window Initialized Successfully.")

    def _initialize_backend_controller(self):
        """Initialize backend controller in background to avoid blocking GUI startup."""
        try:
            self.backend_controller = BackendController()
            self.log_message("Backend Controller Initialized Successfully.")
        except Exception as e:
            self.log_message(
                f"Warning: Backend Controller initialization failed: {e}", "warning"
            )
            # Continue without backend controller - user can retry later

    def start_worker(self, worker_id: str, func: callable, *args, **kwargs):
        """
        Start a worker thread for background processing.
        
        Args:
            worker_id: Unique identifier for the worker
            func: Function to execute in background
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
        """
        try:
            # Extract callback functions from kwargs
            callback = kwargs.pop('callback', None)
            progress_callback = kwargs.pop('progress_callback', None)
            log_message_callback = kwargs.pop('log_message_callback', None)
            cancellation_callback = kwargs.pop('cancellation_callback', None)
            
            # Create a wrapper function that handles callbacks
            def worker_wrapper():
                try:
                    # Add callback functions to kwargs if they exist
                    if progress_callback:
                        kwargs['progress_callback'] = progress_callback
                    if log_message_callback:
                        kwargs['log_message_callback'] = log_message_callback
                    if cancellation_callback:
                        kwargs['cancellation_callback'] = cancellation_callback
                    
                    # Execute the function
                    result = func(*args, **kwargs)
                    
                    # Call the completion callback if provided
                    if callback:
                        # Use QTimer.singleShot to ensure callback runs on main thread
                        QTimer.singleShot(0, lambda: callback(result))
                    
                    return result
                    
                except Exception as e:
                    error_result = {"success": False, "error": str(e)}
                    if callback:
                        QTimer.singleShot(0, lambda: callback(error_result))
                    self.log_message(f"Worker {worker_id} failed: {e}", "error")
                    return error_result
            
            # Submit the worker to the thread pool
            future = self.executor.submit(worker_wrapper)
            
            # Store the future for potential cancellation
            self.active_workers.append((worker_id, future))
            
            self.log_message(f"Started worker {worker_id}")
            
        except Exception as e:
            self.log_message(f"Error starting worker {worker_id}: {e}", "error")
            if callback:
                error_result = {"success": False, "error": str(e)}
                QTimer.singleShot(0, lambda: callback(error_result))

    def start_doc_acquisition(self):
        """Start document acquisition from URLs."""
        w = self.widgets["data_tab"]
        urls = w["doc_urls_input"].toPlainText().strip().split("\n")
        urls = [url.strip() for url in urls if url.strip()]
        if not urls:
            QMessageBox.warning(
                self, "Input Missing", "Please provide at least one URL."
            )
            return

        # Get scraping mode and parameters
        scraping_mode = w["scraping_mode_selector"].currentText()
        max_pages = w["max_pages_spinbox"].value()
        max_depth = w["max_depth_spinbox"].value()
        same_domain_only = w["same_domain_checkbox"].isChecked()

        # Ensure docs directory exists
        os.makedirs(settings.DOCS_DIR, exist_ok=True)

        self.log_message(
            f"Starting {scraping_mode.lower()} acquisition from {len(urls)} URLs..."
        )
        self.log_message(
            f"Parameters: max_pages={max_pages}, max_depth={max_depth}, same_domain_only={same_domain_only}"
        )

        # Update UI state
        self.start_acquisition_button.setEnabled(False)
        self.stop_scraping_button.setEnabled(True)

        # Create progress dialog
        self.progress_dialog = QProgressDialog(
            "Initializing web scraping...", "Cancel", 0, len(urls), self
        )
        self.progress_dialog.setWindowTitle("Web Scraping Progress")
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setAutoClose(False)
        self.progress_dialog.setAutoReset(False)
        self.progress_dialog.setMinimumDuration(0)  # Show immediately
        self.progress_dialog.setValue(0)

        # Define completion callback
        def completion_callback(result: Dict[str, Any]):
            try:
                # Reset UI state
                self.start_acquisition_button.setEnabled(True)
                self.stop_scraping_button.setEnabled(False)

                if self.progress_dialog:
                    self.progress_dialog.close()
                    self.progress_dialog = None

                success_count = result.get("success_count", 0)
                total = result.get("total", 0)
                files = result.get("files", [])
                errors = result.get("errors", [])

                # Show results dialog
                message = "Web Scraping Complete\n\n"
                message += (
                    f"Successfully scraped {success_count} out of {total} URLs.\n\n"
                )

                if files:
                    message += "Scraped documents:\n"
                    for file in files[:5]:  # Show first 5 files
                        message += f"- {os.path.basename(file)}\n"
                    if len(files) > 5:
                        message += f"... and {len(files) - 5} more\n"

                if errors:
                    message += "\nErrors:\n"
                    for error in errors[:5]:  # Show first 5 errors
                        message += f"- {error}\n"
                    if len(errors) > 5:
                        message += f"... and {len(errors) - 5} more errors\n"

                QMessageBox.information(self, "Web Scraping Results", message)
            except Exception as e:
                self.log_message(f"Error in completion callback: {e}")

        # Prepare parameters
        params = {
            "max_pages": max_pages,
            "max_depth": max_depth,
            "same_domain_only": same_domain_only,
            "log_message_callback": self.log_message,
            "cancellation_callback": lambda: self.progress_dialog
            and self.progress_dialog.wasCanceled(),
        }

        try:
            # Start worker based on scraping mode
            worker_id = f"web_scraping_{time.time()}"
            if scraping_mode == "Enhanced (Follow Links)":
                self.start_worker(
                    worker_id,
                    acquire.crawl_docs,
                    urls,
                    settings.DOCS_DIR,  # Use the constant from settings
                    callback=completion_callback,
                    **params,
                )
            else:  # Simple mode
                self.start_worker(
                    worker_id,
                    acquire.crawl_docs_simple,
                    urls,
                    settings.DOCS_DIR,  # Use the constant from settings
                    callback=completion_callback,
                    **params,
                )

            # Connect progress dialog cancel button
            self.progress_dialog.canceled.connect(
                lambda: self.cancel_doc_acquisition(worker_id)
            )

        except Exception as e:
            self.log_message(f"Error starting web scraping: {e}")
            if self.progress_dialog:
                self.progress_dialog.close()
                self.progress_dialog = None
            self.start_scraping_button.setEnabled(True)
            self.stop_scraping_button.setEnabled(False)
            QMessageBox.critical(self, "Error", f"Failed to start web scraping: {e}")

    def cancel_doc_acquisition(self, worker_id: Optional[str] = None):
        """Cancel the document acquisition process."""
        try:
            if worker_id and worker_id in self.active_workers:
                self.executor.submit(lambda: None)  # Placeholder for cancellation

            if self.progress_dialog is not None:
                try:
                    self.progress_dialog.setLabelText("Cancelling web scraping...")
                    self.progress_dialog.setValue(self.progress_dialog.maximum())
                    QApplication.processEvents()  # Ensure UI updates
                except Exception as e:
                    self.log_message(
                        f"Error updating progress dialog during cancellation: {e}",
                        "error",
                    )

            # Reset UI state
            self.start_scraping_button.setEnabled(True)
            self.stop_scraping_button.setEnabled(False)

        except Exception as e:
            self.log_message(f"Error cancelling web scraping: {e}")
            QMessageBox.critical(self, "Error", f"Failed to cancel web scraping: {e}")
        finally:
            if self.progress_dialog is not None:
                try:
                    self.progress_dialog.close()
                except Exception as e:
                    self.log_message(f"Error closing progress dialog: {e}", "error")
                finally:
                    self.progress_dialog = None

    def setup_menu(self):
        """Set up the main menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        # LLM Studio action
        llm_studio_action = file_menu.addAction("Open LLM Studio")
        llm_studio_action.triggered.connect(self.open_llm_studio)

        # Exit action
        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)

        # Help menu
        help_menu = menubar.addMenu("&Help")
        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self.show_about)

    def open_llm_studio(self):
        """Open the LLM Studio window."""
        pass  # Placeholder for now

    def show_about(self):
        """Show the about dialog."""
        QMessageBox.about(
            self,
            "About AI Coder Assistant",
            "AI Coder Assistant\n\n"
            "A powerful AI-powered coding assistant.\n\n"
            "Version: 1.0.0\n"
            "© 2024 AI Coder Assistant Contributors",
        )

    def setup_ui(self):
        """Set up the main window UI."""
        # Set window properties
        self.setWindowTitle("AI Coder Assistant")
        self.setMinimumSize(MAIN_WINDOW_MIN_WIDTH, MAIN_WINDOW_MIN_HEIGHT)

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # Create log output area
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(LOG_OUTPUT_MAX_HEIGHT)
        main_layout.addWidget(self.log_output)

        # Initialize progress dialog as None
        self.progress_dialog = None
        self.report_progress_dialog = None

    def setup_ai_tab(self):
        """Set up the AI tab using the new AI tab widgets."""
        ai_tab = QWidget()
        setup_ai_tab(ai_tab, self)
        self.tab_widget.addTab(ai_tab, "AI Analysis")

    def _on_model_source_changed(self, new_source: str):
        """Handle changes in model source selection."""
        w = self.widgets["ai_tab"]
        model_mode = new_source.lower().replace(" ", "_")

        if model_mode == "ollama":
            # For Ollama models, update the model reference when selection changes
            current_model = w["ollama_model_selector"].currentText()
            if current_model:
                self.current_model_ref = current_model
                self.current_tokenizer_ref = None  # Ollama doesn't need tokenizer
                self.log_message(f"Selected Ollama model: {current_model}")
        elif model_mode == "own_model":
            # For own models, model reference will be set when loading the model
            self.current_model_ref = None
            self.current_tokenizer_ref = None
            self.log_message("Please load a trained model")
        else:
            self.current_model_ref = None
            self.current_tokenizer_ref = None
            self.log_message(f"Unsupported model source: {new_source}")

    def _on_ollama_model_selected(self, model_name: str):
        """Handle Ollama model selection changes."""
        if model_name:
            self.current_model_ref = model_name
            self.current_tokenizer_ref = None  # Ollama doesn't need tokenizer
            self.log_message(f"Selected Ollama model: {model_name}")

    def setup_data_tab(self):
        """Set up the data tab."""
        data_tab = QWidget()
        setup_data_tab(data_tab, self)
        self.tab_widget.addTab(data_tab, "Data")

    def setup_pr_tab(self):
        """Set up the PR tab."""
        pr_tab = QWidget()
        setup_pr_tab(pr_tab, self)
        self.tab_widget.addTab(pr_tab, "PR Management")

    def setup_cloud_models_tab(self):
        """Set up the cloud models tab."""
        cloud_models_tab = CloudModelsTab()
        self.tab_widget.addTab(cloud_models_tab, "Cloud Models")

    def setup_model_manager_tab(self):
        """Set up the model manager tab."""
        llm_manager = LLMManager()
        model_manager_tab = ModelManagerTab(llm_manager)
        self.tab_widget.addTab(model_manager_tab, "Model Manager")

    def setup_ollama_export_tab(self):
        """Set up the Ollama export tab."""
        ollama_export_tab = QWidget()
        setup_ollama_export_tab(ollama_export_tab, self)
        self.tab_widget.addTab(ollama_export_tab, "Ollama Export")

    def setup_continuous_learning_tab(self):
        """Set up the continuous learning tab."""
        continuous_learning_tab = ContinuousLearningTab()
        self.tab_widget.addTab(continuous_learning_tab, "Continuous Learning")

    def setup_code_standards_tab(self):
        """Set up the code standards tab."""
        try:
            if self.backend_controller is not None:
                code_standards_tab = CodeStandardsTab(self.backend_controller)
            else:
                # Create a placeholder tab if backend controller is not ready
                code_standards_tab = QWidget()
                layout = QVBoxLayout()
                label = QLabel("Code Standards\n(Backend not ready - please wait)")
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(label)
                code_standards_tab.setLayout(layout)
            self.tab_widget.addTab(code_standards_tab, "Code Standards")
        except Exception as e:
            self.log_message(f"Error setting up code standards tab: {e}", "error")
            # Create a fallback tab
            fallback_tab = QWidget()
            layout = QVBoxLayout()
            label = QLabel(f"Code Standards\n(Error: {e})")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label)
            fallback_tab.setLayout(layout)
            self.tab_widget.addTab(fallback_tab, "Code Standards")

    def setup_security_intelligence_tab(self):
        """Set up the security intelligence tab."""
        try:
            if self.backend_controller is not None:
                security_intelligence_tab = SecurityIntelligenceTab(
                    self.backend_controller
                )
            else:
                # Create a placeholder tab if backend controller is not ready
                security_intelligence_tab = QWidget()
                layout = QVBoxLayout()
                label = QLabel(
                    "Security Intelligence\n(Backend not ready - please wait)"
                )
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(label)
                security_intelligence_tab.setLayout(layout)
            self.tab_widget.addTab(security_intelligence_tab, "Security Intelligence")
        except Exception as e:
            self.log_message(
                f"Error setting up security intelligence tab: {e}", "error"
            )
            # Create a fallback tab
            fallback_tab = QWidget()
            layout = QVBoxLayout()
            label = QLabel(f"Security Intelligence\n(Error: {e})")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label)
            fallback_tab.setLayout(layout)
            self.tab_widget.addTab(fallback_tab, "Security Intelligence")

    def setup_settings_tab(self):
        """Set up the settings tab."""
        try:
            if self.backend_controller is not None:
                settings_tab = SettingsTab(self.backend_controller)
            else:
                # Create a placeholder tab if backend controller is not ready
                settings_tab = QWidget()
                layout = QVBoxLayout()
                label = QLabel("Settings\n(Backend not ready - please wait)")
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(label)
                settings_tab.setLayout(layout)
            self.tab_widget.addTab(settings_tab, "Settings")
        except Exception as e:
            self.log_message(f"Error setting up settings tab: {e}", "error")
            # Create a fallback tab
            fallback_tab = QWidget()
            layout = QVBoxLayout()
            label = QLabel(f"Settings\n(Error: {e})")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label)
            fallback_tab.setLayout(layout)
            self.tab_widget.addTab(fallback_tab, "Settings")

    def setup_performance_optimization_tab(self):
        """Set up the performance optimization tab."""
        performance_optimization_tab = PerformanceOptimizationTab()
        self.tab_widget.addTab(performance_optimization_tab, "Performance Optimization")

    def setup_advanced_refactoring_tab(self):
        """Set up the advanced refactoring tab."""
        advanced_refactoring_tab = RefactoringTab()
        self.tab_widget.addTab(advanced_refactoring_tab, "Advanced Refactoring")

    def setup_advanced_analytics_tab(self):
        """Set up the advanced analytics tab."""
        advanced_analytics_tab = AdvancedAnalyticsTab()
        self.tab_widget.addTab(advanced_analytics_tab, "Advanced Analytics")

    def setup_web_server_tab(self):
        """Set up the web server tab."""
        web_server_tab = WebServerTab()
        self.tab_widget.addTab(web_server_tab, "Web Server")

    def setup_collaboration_tab(self):
        """Set up the collaboration tab."""
        collaboration_tab = CollaborationTab()
        self.tab_widget.addTab(collaboration_tab, "Collaboration")

    def _connect_signals(self):
        """Connect all UI signals to their respective slots."""
        logger.debug("Connecting UI signals...")

        try:
            # Connect signals for AI tab widgets
            if "ai_tab" in self.widgets:
                w = self.widgets["ai_tab"]
                
                # Connect model-related signals
                if "refresh_models_button" in w:
                    w["refresh_models_button"].clicked.connect(self.populate_ollama_models)
                if "load_model_button" in w:
                    w["load_model_button"].clicked.connect(self.load_trained_model)
                if "browse_button" in w:
                    w["browse_button"].clicked.connect(self.select_scan_directory)
                
                # Connect scan-related signals (these are already connected in ai_tab_widgets.py)
                # The AI tab widgets handle their own signal connections
                
                # Connect model selection signals
                if "model_source_selector" in w:
                    w["model_source_selector"].currentTextChanged.connect(
                        self._on_model_source_changed
                    )
                if "ollama_model_selector" in w:
                    w["ollama_model_selector"].currentTextChanged.connect(
                        self._on_ollama_model_selected
                    )
            
            # Connect other signals
            self.scan_progress_updated.connect(self._update_scan_progress_safe)
            self.scan_completed.connect(self._handle_scan_complete_ui)
            
            logger.debug("UI signals connected successfully.")

        except Exception as e:
            logger.error(f"Error connecting UI signals: {e}")
            # Don't raise the exception to prevent app startup failure
            # Just log the error and continue

    def populate_ollama_models(self):
        """Populate the Ollama model selector with available models."""
        try:
            models = get_available_models_sync()
            self.widgets["ai_tab"]["ollama_model_selector"].clear()
            if models:
                self.widgets["ai_tab"]["ollama_model_selector"].addItems(models)
                self.log_message(f"Found {len(models)} Ollama models")
            else:
                self.log_message("No Ollama models found")
        except Exception as e:
            self.log_message(f"Error getting Ollama models: {e}")

    def load_trained_model(self):
        """Load a custom trained model from file."""
        try:
            # Open file dialog to select model file
            model_file, _ = QFileDialog.getOpenFileName(
                self,
                "Select Trained Model File",
                "",
                "Model Files (*.pth *.pt *.bin *.safetensors);;All Files (*)",
            )

            if not model_file:
                return

            self.log_message(f"Loading trained model from: {model_file}")

            # Update UI to show loading state
            self.widgets["ai_tab"]["own_model_status_label"].setText("Loading...")
            self.widgets["ai_tab"]["load_model_button"].setEnabled(False)

            # Start worker to load the model
            self.start_worker(
                "load_model",
                self._load_model_worker,
                model_file,
                callback=self._on_model_loaded,
                error_callback=self._on_model_load_error,
            )

        except Exception as e:
            self.log_message(f"Error starting model load: {e}")
            self.widgets["ai_tab"]["own_model_status_label"].setText("Load Failed")
            self.widgets["ai_tab"]["load_model_button"].setEnabled(True)

    def _load_model_worker(self, model_file: str):
        """Worker function to load the trained model."""
        try:
            # This is a placeholder implementation
            # In a real implementation, you would load the model here
            # For now, we'll just simulate loading
            import time

            time.sleep(2)  # Simulate loading time

            return {
                "success": True,
                "model_file": model_file,
                "model_name": os.path.basename(model_file),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _on_model_loaded(self, result):
        """Handle successful model loading."""
        try:
            if result.get("success"):
                model_name = result.get("model_name", "Unknown Model")
                self.current_model_ref = result.get("model_file")
                self.current_tokenizer_ref = None  # Set if you have a tokenizer
                self.widgets["ai_tab"]["own_model_status_label"].setText(
                    f"Loaded: {model_name}"
                )
                self.log_message(f"Successfully loaded model: {model_name}")
            else:
                self.widgets["ai_tab"]["own_model_status_label"].setText("Load Failed")
                self.log_message(
                    f"Failed to load model: {result.get('error', 'Unknown error')}"
                )
        except Exception as e:
            self.log_message(f"Error handling model load result: {e}")
        finally:
            self.widgets["ai_tab"]["load_model_button"].setEnabled(True)

    def _on_model_load_error(self, error):
        """Handle model loading errors."""
        try:
            self.widgets["ai_tab"]["own_model_status_label"].setText("Load Failed")
            self.widgets["ai_tab"]["load_model_button"].setEnabled(True)
            self.log_message(f"Model loading error: {error}")
        except Exception as e:
            self.log_message(f"Error handling model load error: {e}")

    def select_scan_directory(self):
        """Select directory to scan for code analysis."""
        # Prevent multiple dialogs from opening
        if self._directory_dialog_open:
            return
            
        try:
            self._directory_dialog_open = True
            
            directory = QFileDialog.getExistingDirectory(
                self, 
                "Select Directory to Scan",
                options=QFileDialog.Option.ShowDirsOnly
            )
            
            if directory and os.path.exists(directory):
                self.scan_directory = directory
                
                # Update the project directory field in the AI tab immediately
                if "ai_tab" in self.widgets and "project_dir_edit" in self.widgets["ai_tab"]:
                    self.widgets["ai_tab"]["project_dir_edit"].setText(directory)
                    # Force the field to update visually
                    self.widgets["ai_tab"]["project_dir_edit"].repaint()
                
                # Update other directory fields if they exist
                if hasattr(self, "scan_dir_entry"):
                    self.scan_dir_entry.setText(directory)
                
                self.log_message(f"Selected scan directory: {directory}")
                
                # Update scan directory for immediate use
                self.scan_directory = directory
                
            elif directory:
                self.log_message(f"Selected directory does not exist: {directory}", "warning")
                
        except Exception as e:
            self.log_message(f"Error selecting directory: {e}", "error")
        finally:
            # Always reset the flag
            self._directory_dialog_open = False

    def select_local_corpus_dir(self):
        """Select local corpus directory."""
        dir_name = QFileDialog.getExistingDirectory(
            self, "Select Local Corpus Directory"
        )
        if dir_name:
            w = self.widgets["data_tab"]
            w["local_files_label"].setText(f"Selected: {os.path.basename(dir_name)}")
            # Store the directory path for later use
            self.local_corpus_dir = dir_name

    def start_preprocessing(self):
        """Start preprocessing of documents."""
        w = self.widgets["data_tab"]
        reset_db = w["knowledge_mode_selector"].currentText().startswith("Reset")

        self.log_message("Starting preprocessing...")

        # Create progress dialog
        self.progress_dialog = QProgressDialog(
            "Preprocessing documents...", "Cancel", 0, 100, self
        )
        self.progress_dialog.setWindowTitle("Preprocessing Progress")
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setAutoClose(False)
        self.progress_dialog.setAutoReset(False)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.setValue(0)

        # Start preprocessing worker
        worker_id = f"preprocessing_{time.time()}"
        self.start_worker(
            worker_id,
            preprocess.preprocess_all_docs,
            reset_db=reset_db,
            progress_callback=self.update_preprocess_progress,
            log_message_callback=self.log_message,
            cancellation_callback=lambda: self.progress_dialog
            and self.progress_dialog.wasCanceled(),
        )

        # Connect progress dialog cancel button
        self.progress_dialog.canceled.connect(lambda: self.cancel_worker(worker_id))

    def review_next_suggestion(self):
        """Start reviewing the next suggestion in the list."""
        if not hasattr(self, "suggestion_list") or not self.suggestion_list:
            QMessageBox.warning(
                self,
                "No Suggestions",
                "Please run a scan first to generate suggestions.",
            )
            return

        if not hasattr(self, "current_suggestion_index"):
            self.current_suggestion_index = 0

        if self.current_suggestion_index >= len(self.suggestion_list):
            QMessageBox.information(
                self, "Review Complete", "All suggestions have been reviewed."
            )
            self.current_suggestion_index = 0
            return

        suggestion = self.suggestion_list[self.current_suggestion_index]

        # Get model settings
        model_mode = (
            self.widgets["ai_tab"]["model_source_selector"]
            .currentText()
            .lower()
            .replace(" ", "_")
        )
        model_ref = self.current_model_ref
        tokenizer_ref = self.current_tokenizer_ref

        # Start worker to get AI explanation
        self.log_message(
            f"Getting AI explanation for suggestion {self.current_suggestion_index + 1}/{len(self.suggestion_list)}"
        )
        self.start_worker(
            "get_explanation",
            ai_tools.get_ai_explanation,
            suggestion,
            model_mode,
            model_ref,
            tokenizer_ref,
            progress_callback=lambda c, t, m: None,  # No progress needed for single explanation
            log_message_callback=self.log_message,
        )

    def apply_suggestion(self, suggestion):
        """Apply a code suggestion to the file."""
        try:
            file_path = suggestion.get("file_path")
            line_number = suggestion.get("line_number", 0)
            suggested_code = suggestion.get("suggested_improvement", "")

            if (
                not file_path
                or not suggested_code
                or suggested_code == "No suggestion available"
            ):
                self.log_message("No valid suggestion to apply")
                return

            # Read the file
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # Apply the suggestion (replace the problematic line)
            if 0 <= line_number < len(lines):
                lines[line_number] = suggested_code + "\n"

                # Write back to file
                with open(file_path, "w", encoding="utf-8") as f:
                    f.writelines(lines)

                self.log_message(f"Applied suggestion to {file_path}:{line_number + 1}")
            else:
                self.log_message(
                    f"Invalid line number {line_number} for file {file_path}"
                )

        except Exception as e:
            self.log_message(f"Error applying suggestion: {e}")

    def start_youtube_transcription(self):
        youtube_url = self.youtube_url_entry.text()
        if not youtube_url:
            return
        self.start_worker(
            "transcribe_youtube", ai_tools.transcribe_youtube_tool, youtube_url
        )

    @pyqtSlot(str)
    def log_message(self, message: str, level: str = "info") -> None:
        """Append a message to the log output widget."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}][{level.upper()}] {message}"
        self.log_output.append(formatted_message)
        # Also log to file
        if level == "error":
            logger.error(message)
        else:
            logger.info(message)

    def _process_log_queue(self):
        """Process queued log messages on the main thread."""
        try:
            with QMutexLocker(self._log_mutex):
                messages = self._log_queue.copy()
                self._log_queue.clear()

            # Process all queued messages
            for message in messages:
                self._log_message_safe(message)

        except Exception as e:
            print(f"Error processing log queue: {e}")

    def _log_message_safe(self, message: str) -> None:
        """Thread-safe log message implementation (called on main thread)."""
        try:
            if hasattr(self, "log_output") and self.log_output:
                self.log_output.append(message)
                self.log_output.verticalScrollBar().setValue(
                    self.log_output.verticalScrollBar().maximum()
                )
        except Exception as e:
            print(f"Error in thread-safe log message: {e}")
            print(f"Original message: {message}")

    def start_report_generation(self):
        """Start generating a full markdown report with robust validation."""
        w = self.widgets["ai_tab"]
        try:
            # Check if we have scan results to report
            if not hasattr(self, "scan_results") or not self.scan_results:
                QMessageBox.warning(
                    self,
                    "No Data for Report",
                    "Please run a scan first to generate data for the report.",
                )
                return
            
            # Get issues from scan results
            issues = []
            if isinstance(self.scan_results, dict) and "issues" in self.scan_results:
                # New quick scan format
                issues = self.scan_results["issues"]
            elif isinstance(self.scan_results, list):
                # Legacy format
                issues = self.scan_results
            
            if not issues:
                QMessageBox.warning(
                    self,
                    "No Issues for Report",
                    "No issues found in the scan results to include in the report.",
                )
                return

            # Validate model selection
            if not w["model_source_selector"]:
                QMessageBox.warning(
                    self,
                    "Configuration Error",
                    "Model source selector not found. Please restart the application.",
                )
                return

            # Get model settings with validation
            model_mode = (
                w["model_source_selector"].currentText().lower().replace(" ", "_")
            )
            model_ref = getattr(self, "current_model_ref", None)
            tokenizer_ref = getattr(self, "current_tokenizer_ref", None)

            # Validate model reference for AI-enhanced reports
            if model_mode == "ollama" and (not model_ref or model_ref is None):
                QMessageBox.warning(
                    self,
                    "No Model Selected",
                    "For AI-enhanced reports, please select an Ollama model first.\n\n"
                    "1. Go to the Model Management section\n"
                    "2. Select 'Ollama' as the model source\n"
                    "3. Choose a model from the dropdown\n"
                    "4. Try report generation again",
                )
                return

            # Create progress dialog
            self.report_progress_dialog = QProgressDialog(
                "Generating report...", "Cancel", 0, 100, self
            )
            self.report_progress_dialog.setWindowTitle("Report Generation")
            self.report_progress_dialog.setAutoClose(True)
            self.report_progress_dialog.setAutoReset(True)
            self.report_progress_dialog.setMinimumDuration(0)
            self.report_progress_dialog.setValue(0)
            self.report_progress_dialog.show()

            # Start worker to generate report
            self.log_message(f"Starting report generation for {len(issues)} issues...")

            def report_completion_callback(result):
                """Handle report generation completion."""
                try:
                    # Close progress dialog
                    if hasattr(self, "report_progress_dialog") and self.report_progress_dialog:
                        self.report_progress_dialog.close()
                        self.report_progress_dialog = None
                    
                    if result and len(result) >= 2:
                        markdown_report, training_data = result
                        
                        # Display success message with summary
                        report_summary = f"""
Report Generation Complete!

📊 Summary:
• Total Issues Processed: {len(issues)}
• Report Size: {len(markdown_report)} characters
• Training Data Records: {len(training_data.split(chr(10))) if training_data else 0}

📄 Report Content:
{markdown_report[:500]}...

✅ The report has been generated successfully!
"""
                        
                        # Show the report in a dialog
                        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout
                        
                        report_dialog = QDialog(self)
                        report_dialog.setWindowTitle("AI Code Review Report")
                        report_dialog.resize(800, 600)
                        
                        layout = QVBoxLayout(report_dialog)
                        
                        # Add summary text
                        summary_text = QTextEdit()
                        summary_text.setPlainText(report_summary)
                        summary_text.setMaximumHeight(200)
                        summary_text.setReadOnly(True)
                        layout.addWidget(summary_text)
                        
                        # Add full report
                        report_text = QTextEdit()
                        report_text.setPlainText(markdown_report)
                        report_text.setReadOnly(True)
                        layout.addWidget(report_text)
                        
                        # Add buttons
                        button_layout = QHBoxLayout()
                        
                        save_button = QPushButton("Save Report")
                        def save_report():
                            from PyQt6.QtWidgets import QFileDialog
                            file_path, _ = QFileDialog.getSaveFileName(
                                report_dialog, 
                                "Save Report", 
                                "ai_code_review_report.md",
                                "Markdown Files (*.md);;All Files (*)"
                            )
                            if file_path:
                                try:
                                    with open(file_path, 'w', encoding='utf-8') as f:
                                        f.write(markdown_report)
                                    self.log_message(f"Report saved to: {file_path}")
                                    QMessageBox.information(report_dialog, "Success", f"Report saved to:\n{file_path}")
                                except Exception as e:
                                    QMessageBox.warning(report_dialog, "Error", f"Failed to save report: {e}")
                        
                        save_button.clicked.connect(save_report)
                        button_layout.addWidget(save_button)
                        
                        close_button = QPushButton("Close")
                        close_button.clicked.connect(report_dialog.accept)
                        button_layout.addWidget(close_button)
                        
                        layout.addLayout(button_layout)
                        
                        # Show the dialog
                        report_dialog.exec()
                        
                        self.log_message("Report generation completed successfully!")
                        
                    else:
                        QMessageBox.warning(
                            self,
                            "Report Generation Error",
                            "Report generation completed but no valid result was returned."
                        )
                        self.log_message("Report generation completed with no valid result", "warning")
                        
                except Exception as e:
                    self.log_message(f"Error in report completion callback: {e}", "error")
                    QMessageBox.critical(
                        self,
                        "Report Error",
                        f"Error processing report results: {e}"
                    )

            self.start_worker(
                "generate_report",
                ai_tools.generate_report_and_training_data,
                issues,  # Pass the issues directly
                model_mode,
                model_ref,
                tokenizer_ref,
                progress_callback=self.update_report_progress,
                log_message_callback=self.log_message,
                callback=report_completion_callback
            )

        except Exception as e:
            self.log_message(f"Error starting report generation: {e}")
            QMessageBox.critical(
                self,
                "Report Generation Error",
                f"Failed to start report generation:\n{str(e)}\n\nPlease check the logs for more details.",
            )

    def update_report_progress(self, current: int, total: int, message: str):
        """Update report generation progress."""
        if hasattr(self, "report_progress_dialog") and self.report_progress_dialog:
            self.report_progress_dialog.setRange(0, total)
            self.report_progress_dialog.setValue(current)
            self.report_progress_dialog.setLabelText(message)
            if current >= total:
                self.report_progress_dialog.setValue(total)

    def navigate_to_url(self):
        url_text = self.url_bar.text()
        if not url_text.startswith(("http://", "https://")):
            url_text = "https://" + url_text
        self.browser.setUrl(QUrl(url_text))

    def update_url_bar(self, qurl):
        self.url_bar.setText(qurl.toString())

    def closeEvent(self, event):
        """Handle application shutdown and cleanup worker threads."""
        self.log_message("Shutting down...")
        self.executor.shutdown(wait=False, cancel_futures=True)
        event.accept()

    def stop_scan(self):
        """Stop the current scan operation."""
        try:
            # Reset scan in progress flag
            self._scan_in_progress = False
            
            # Cancel the scanner service
            if hasattr(self, "scanner_service"):
                self.scanner_service.cancel_scan()

            # Cancel the current worker if it exists
            if hasattr(self, "current_worker_id") and self.current_worker_id:
                self.log_message("Stopping scan operation...")
                # Cancel the future if it exists
                if hasattr(self, "current_scan_future") and self.current_scan_future:
                    self.current_scan_future.cancel()
                self.current_worker_id = None
                self.current_scan_future = None

            # Reset UI state
            w = self.widgets["ai_tab"]
            w["start_quick_scan_button"].setEnabled(True)
            w["stop_scan_button"].setEnabled(False)

            # Close progress dialog if open
            if self.progress_dialog is not None:
                try:
                    self.progress_dialog.close()
                except Exception as e:
                    self.log_message(f"Error closing progress dialog: {e}", "error")
                finally:
                    self.progress_dialog = None

            # Force garbage collection
            import gc

            gc.collect()

            self.log_message("Scan operation stopped by user")

        except Exception as e:
            # Reset scan in progress flag on error
            self._scan_in_progress = False
            self.log_message(f"Error stopping scan: {e}", "error")

    def start_scan(self):
        """Legacy method - redirects to start_quick_scan for compatibility."""
        self.start_quick_scan()

    def start_ai_enhancement(self):
        """Legacy method - redirects to enhance_all_issues for compatibility."""
        self.enhance_all_issues()

    def start_quick_scan(self):
        """Start a quick, local scan without AI enhancement."""
        # Prevent multiple scans from running simultaneously
        if self._scan_in_progress:
            self.log_message("A scan is already in progress. Please wait for it to complete.", "warning")
            return
            
        w = self.widgets["ai_tab"]
        w["scan_status_label"].setText("Starting quick scan...")
        w["enhance_all_button"].setEnabled(False)

        # Clear previous results
        w["results_table"].setRowCount(0)

        # Disable start button and enable stop button
        w["start_quick_scan_button"].setEnabled(False)
        w["stop_scan_button"].setEnabled(True)

        self.scan_directory = w["project_dir_edit"].text()
        if not os.path.exists(self.scan_directory):
            QMessageBox.warning(
                self,
                "Invalid Directory",
                f"The directory '{self.scan_directory}' does not exist.",
            )
            # Re-enable start button and disable stop button
            w["start_quick_scan_button"].setEnabled(True)
            w["stop_scan_button"].setEnabled(False)
            return

        # Set scan in progress flag
        self._scan_in_progress = True

        # Create progress dialog
        self.progress_dialog = QProgressDialog(
            "Performing quick scan...", "Cancel", 0, 100, self
        )
        self.progress_dialog.setWindowTitle("Quick Scan Progress")
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.show()

        # Get scan parameters
        include_patterns = (
            w["include_patterns_edit"].text().split(",")
            if w["include_patterns_edit"].text()
            else []
        )
        exclude_patterns = (
            w["exclude_patterns_edit"].text().split(",")
            if w["exclude_patterns_edit"].text()
            else []
        )

        # Use the new BackendController for quick scan
        try:
            if self.backend_controller:
                result = self.backend_controller.start_quick_scan(
                    self.scan_directory, 
                    include_patterns, 
                    exclude_patterns
                )
                self._handle_quick_scan_completion(result)
            else:
                # Fallback to old method if backend controller not available
                self._perform_quick_scan_worker_legacy(
                    self.scan_directory, 
                    include_patterns, 
                    exclude_patterns
                )
        except Exception as e:
            self.log_message(f"Error starting quick scan: {e}", "error")
            QMessageBox.warning(self, "Scan Error", f"Failed to start quick scan: {e}")
            # Re-enable start button and disable stop button
            w["start_quick_scan_button"].setEnabled(True)
            w["stop_scan_button"].setEnabled(False)

    def _handle_quick_scan_completion(self, result):
        """Handle completion of quick scan."""
        try:
            # Reset scan in progress flag
            self._scan_in_progress = False
            
            w = self.widgets["ai_tab"]
            
            # Close progress dialog
            if self.progress_dialog:
                self.progress_dialog.close()
                self.progress_dialog = None

            # Re-enable start button and disable stop button
            w["start_quick_scan_button"].setEnabled(True)
            w["stop_scan_button"].setEnabled(False)

            if result and isinstance(result, dict):
                issues = result.get("issues", [])
                total_files = result.get("total_files", 0)
                
                # Update status
                w["scan_status_label"].setText(f"Quick scan completed. Found {len(issues)} issues.")
                
                # Populate results table
                from src.frontend.ui.ai_tab_widgets import populate_scan_results_table
                populate_scan_results_table(w, issues)
                
                self.log_message(f"Quick scan completed. Found {len(issues)} issues.")
                
                # Enable post-scan buttons
                w["enhance_all_button"].setEnabled(len(issues) > 0)
                w["export_results_button"].setEnabled(len(issues) > 0)
                
            else:
                w["scan_status_label"].setText("Quick scan failed or was cancelled.")
                self.log_message("Quick scan failed or was cancelled.", "warning")
                
        except Exception as e:
            # Reset scan in progress flag on error
            self._scan_in_progress = False
            self.log_message(f"Error handling scan completion: {e}", "error")
            w = self.widgets["ai_tab"]
            w["start_quick_scan_button"].setEnabled(True)
            w["stop_scan_button"].setEnabled(False)
            w["scan_status_label"].setText("Scan failed with error.")

    def _perform_quick_scan_worker_legacy(self, directory: str, include_patterns: List[str], 
                                        exclude_patterns: List[str], progress_callback=None, 
                                        log_message_callback=None, cancellation_callback=None):
        """Legacy worker function to perform quick scan."""
        try:
            from src.backend.services.intelligent_analyzer import IntelligentCodeAnalyzer
            
            analyzer = IntelligentCodeAnalyzer()
            all_issues = []
            
            # Get files to scan
            files_to_scan = []
            for root, dirs, files in os.walk(directory):
                # Skip excluded directories
                dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', 'node_modules', '.venv', 'venv'}]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    # Check if file matches include patterns
                    if any(file.endswith(pattern.strip()) for pattern in include_patterns):
                        # Check if file should be excluded
                        if not any(exclude in file_path for exclude in exclude_patterns):
                            files_to_scan.append(file_path)
            
            total_files = len(files_to_scan)
            
            for i, file_path in enumerate(files_to_scan):
                if cancellation_callback and cancellation_callback():
                    return {"cancelled": True}
                
                if progress_callback:
                    progress_callback(i, total_files, f"Scanning {os.path.basename(file_path)}")
                
                if log_message_callback:
                    log_message_callback(f"Scanning {file_path}")
                
                # Perform quick scan on file
                file_issues = analyzer.perform_quick_scan(file_path)
                
                # Add file path to each issue
                for issue in file_issues:
                    issue["file_path"] = file_path
                
                all_issues.extend(file_issues)
            
            if progress_callback:
                progress_callback(total_files, total_files, "Quick scan completed")
            
            return {
                "success": True,
                "issues": all_issues,
                "total_files": total_files,
                "cancelled": False
            }
            
        except Exception as e:
            if log_message_callback:
                log_message_callback(f"Error during quick scan: {e}")
            return {"success": False, "error": str(e)}

    def enhance_all_issues(self):
        """Enhance all issues with AI analysis."""
        try:
            w = self.widgets["ai_tab"]
            table = w["results_table"]
            
            if table.rowCount() == 0:
                QMessageBox.information(self, "No Issues", "No issues to enhance.")
                return
            
            reply = QMessageBox.question(
                self, "Enhance All Issues", 
                f"Enhance all {table.rowCount()} issues with AI analysis? This may take some time.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                w["scan_status_label"].setText("Enhancing all issues with AI...")
                
                # Collect all issues
                issues = []
                for row in range(table.rowCount()):
                    file_item = table.item(row, 0)
                    if file_item:
                        issue_data = file_item.data(Qt.ItemDataRole.UserRole)
                        if issue_data:
                            issues.append(issue_data)
                
                # Start enhancement for each issue
                for i, issue_data in enumerate(issues):
                    self.current_issue_data = issue_data  # Store for callback
                    self.enhance_issue_with_ai(issue_data)
                    
        except Exception as e:
            self.log_message(f"Error enhancing all issues: {e}")
            QMessageBox.critical(self, "Error", f"Failed to enhance all issues: {e}")

    def enhance_issue_with_ai(self, issue_data: Dict[str, Any]):
        """Enhance a single issue with AI analysis."""
        try:
            w = self.widgets["ai_tab"]
            w["scan_status_label"].setText(f"Enhancing issue on line {issue_data.get('line', 0)}...")
            
            # Get enhancement type (default to code improvement)
            enhancement_type = "code_improvement"
            
            # Start AI enhancement using the existing worker infrastructure
            worker_id = f"ai_enhancement_{time.time()}"
            self.start_worker(
                worker_id,
                self._perform_ai_enhancement_worker,
                issue_data=issue_data,
                enhancement_type=enhancement_type,
                callback=self.on_enhancement_complete,
                error_callback=self.on_enhancement_error
            )
            
        except Exception as e:
            self.log_message(f"Error starting AI enhancement: {e}")
            QMessageBox.critical(self, "Error", f"Failed to start AI enhancement: {e}")

    def _perform_ai_enhancement_worker(self, issue_data: Dict[str, Any], enhancement_type: str, 
                                     progress_callback=None, log_message_callback=None):
        """Worker function for AI enhancement."""
        try:
            if log_message_callback:
                log_message_callback(f"Starting AI enhancement for issue: {issue_data.get('issue', 'Unknown')}")
            
            # Get the backend controller for AI enhancement
            from src.frontend.controllers.backend_controller import BackendController
            controller = BackendController()
            
            # Perform AI enhancement
            result = controller.get_ai_enhancement(
                issue_data=issue_data,
                enhancement_type=enhancement_type
            )
            
            if log_message_callback:
                log_message_callback("AI enhancement completed successfully")
            
            return {
                "success": True,
                "result": result,
                "issue_data": issue_data
            }
            
        except Exception as e:
            if log_message_callback:
                log_message_callback(f"Error during AI enhancement: {e}")
            return {
                "success": False,
                "error": str(e),
                "issue_data": issue_data
            }

    def on_enhancement_complete(self, result):
        """Handle AI enhancement completion."""
        try:
            w = self.widgets["ai_tab"]
            w["scan_status_label"].setText("AI enhancement complete")
            
            if result.get("success", False):
                # Show the enhancement dialog
                from src.frontend.ui.suggestion_dialog import AIEnhancementDialog
                dialog = AIEnhancementDialog(result["issue_data"], result["result"], self)
                dialog.exec()
            else:
                QMessageBox.warning(self, "Enhancement Error", f"AI enhancement failed: {result.get('error', 'Unknown error')}")
            
        except Exception as e:
            self.log_message(f"Error handling enhancement completion: {e}")

    def on_enhancement_error(self, error):
        """Handle AI enhancement error."""
        self.log_message(f"AI enhancement error: {error}")
        QMessageBox.warning(self, "Enhancement Error", f"AI enhancement failed: {error}")

    def _handle_quick_scan_results(self, result: Dict[str, Any]):
        """Handle quick scan results and update UI."""
        w = self.widgets["ai_tab"]
        
        issues = result.get("issues", [])
        
        if not issues:
            w["scan_status_label"].setText("Status: Quick scan completed - No issues found")
            return
        
        # Update the results table
        from src.frontend.ui.ai_tab_widgets import populate_scan_results_table, update_scan_summary
        
        populate_scan_results_table(w, issues)
        update_scan_summary(w, issues)
        
        w["scan_status_label"].setText(f"Status: Quick scan completed - {len(issues)} issues found")
        
        self.log_message(f"Quick scan completed. Found {len(issues)} issues.")

    def _get_language_from_file_path(self, file_path: str) -> str:
        """Get language from file path."""
        ext = file_path.lower().split('.')[-1]
        language_map = {
            'py': 'python',
            'js': 'javascript',
            'ts': 'typescript',
            'java': 'java',
            'cpp': 'cpp',
            'c': 'c',
            'h': 'c',
            'hpp': 'cpp'
        }
        return language_map.get(ext, 'unknown')

    def update_scan_progress(self, current: int, total: int, message: str):
        """
        Thread-safe method to update scan progress by emitting a signal.
        This method is called from the background thread.
        """
        self.scan_progress_updated.emit(current, total, message)

    @pyqtSlot(int, int, str)
    def _update_scan_progress_safe(self, current: int, total: int, message: str):
        """Updates the progress dialog from the main UI thread."""
        if self.progress_dialog is not None:
            try:
                self.progress_dialog.setMaximum(total)
                self.progress_dialog.setValue(current)
                self.progress_dialog.setLabelText(message)
            except Exception as e:
                # Log error and clean up the dialog if it's in an invalid state
                self.log_message(f"Error updating progress dialog: {e}", "error")
                self.progress_dialog = None

    @pyqtSlot(list)
    def _handle_scan_complete_ui(self, result):
        """Update the UI with scan results, running in the main thread."""
        try:
            self.scan_results = result  # Store results
            
            # Handle different result formats
            if isinstance(result, dict) and "issues" in result:
                # New quick scan format
                self._handle_quick_scan_results(result)
            else:
                # Old format - list of file results
                self._handle_legacy_scan_results(result)
                
        except Exception as e:
            self.log_message(f"Error displaying scan results: {e}", "error")
        finally:
            # Reset scan button states
            w = self.widgets["ai_tab"]
            w["start_quick_scan_button"].setEnabled(True)
            w["stop_scan_button"].setEnabled(False)

            if self.progress_dialog is not None:
                try:
                    QTimer.singleShot(0, self.progress_dialog.close)
                except Exception as e:
                    self.log_message(f"Error closing progress dialog: {e}", "error")
                finally:
                    self.progress_dialog = None

            # Enable post-scan buttons only if there are results
            if self.scan_results:
                self._enable_post_scan_buttons(True)
            else:
                self._enable_post_scan_buttons(False)

    def _handle_legacy_scan_results(self, result: List[Dict[str, Any]]):
        """Handle results from legacy scan format."""
        w = self.widgets["ai_tab"]
        # Update the results table instead of using scan_results_text
        from src.frontend.ui.ai_tab_widgets import populate_scan_results_table, update_scan_summary
        
        # Convert legacy format to new format
        issues = []
        for file_result in result:
            file_path = file_result.get("file_path", "N/A")
            file_issues = file_result.get("issues", [])
            for issue in file_issues:
                issue["file"] = file_path
                issues.append(issue)
        
        populate_scan_results_table(w, issues)
        update_scan_summary(w, issues)
        self.log_message(f"Scan finished. Displaying {len(issues)} issues.")

    def _enable_post_scan_buttons(self, enabled: bool):
        """Enable or disable buttons that require scan results."""
        w = self.widgets["ai_tab"]
        w["enhance_all_button"].setEnabled(enabled)
        w["export_results_button"].setEnabled(enabled)

    def start_base_training(self):
        """Start base model training from corpus."""
        try:
            self.log_message("Starting base model training...")
            
            # Create progress dialog
            self.progress_dialog = QProgressDialog(
                "Training base model...", "Cancel", 0, 100, self
            )
            self.progress_dialog.setWindowTitle("Model Training Progress")
            self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            self.progress_dialog.setAutoClose(False)
            self.progress_dialog.setAutoReset(False)
            self.progress_dialog.setMinimumDuration(0)
            self.progress_dialog.setValue(0)
            
            def completion_callback(result: Dict[str, Any]):
                try:
                    if self.progress_dialog:
                        self.progress_dialog.close()
                        self.progress_dialog = None
                    
                    if result.get("success", False):
                        self.log_message("Base model training completed successfully!")
                        QMessageBox.information(self, "Training Complete", 
                                              "Base model training completed successfully!")
                    else:
                        error_msg = result.get("error", "Unknown error")
                        self.log_message(f"Base model training failed: {error_msg}", "error")
                        QMessageBox.warning(self, "Training Failed", 
                                          f"Base model training failed: {error_msg}")
                        
                except Exception as e:
                    self.log_message(f"Error in training completion callback: {e}", "error")
            
            # Start training in background
            worker_id = f"base_training_{time.time()}"
            self.start_worker(
                worker_id,
                self._perform_base_training_worker,
                callback=completion_callback
            )
            
        except Exception as e:
            self.log_message(f"Error starting base training: {e}", "error")
            QMessageBox.warning(self, "Training Error", f"Failed to start training: {e}")

    def start_finetuning(self):
        """Start model finetuning with feedback."""
        try:
            self.log_message("Starting model finetuning...")
            
            # Create progress dialog
            self.progress_dialog = QProgressDialog(
                "Finetuning model...", "Cancel", 0, 100, self
            )
            self.progress_dialog.setWindowTitle("Model Finetuning Progress")
            self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            self.progress_dialog.setAutoClose(False)
            self.progress_dialog.setAutoReset(False)
            self.progress_dialog.setMinimumDuration(0)
            self.progress_dialog.setValue(0)
            
            def completion_callback(result: Dict[str, Any]):
                try:
                    if self.progress_dialog:
                        self.progress_dialog.close()
                        self.progress_dialog = None
                    
                    if result.get("success", False):
                        self.log_message("Model finetuning completed successfully!")
                        QMessageBox.information(self, "Finetuning Complete", 
                                              "Model finetuning completed successfully!")
                    else:
                        error_msg = result.get("error", "Unknown error")
                        self.log_message(f"Model finetuning failed: {error_msg}", "error")
                        QMessageBox.warning(self, "Finetuning Failed", 
                                          f"Model finetuning failed: {error_msg}")
                        
                except Exception as e:
                    self.log_message(f"Error in finetuning completion callback: {e}", "error")
            
            # Start finetuning in background
            worker_id = f"finetuning_{time.time()}"
            self.start_worker(
                worker_id,
                self._perform_finetuning_worker,
                callback=completion_callback
            )
            
        except Exception as e:
            self.log_message(f"Error starting finetuning: {e}", "error")
            QMessageBox.warning(self, "Finetuning Error", f"Failed to start finetuning: {e}")

    def _perform_base_training_worker(self, progress_callback=None, log_message_callback=None):
        """Worker function for base model training."""
        try:
            if log_message_callback:
                log_message_callback("Initializing base model training...")
            
            if progress_callback:
                progress_callback(10, 100, "Loading training data...")
            
            # TODO: Implement actual base training logic
            # For now, simulate training process
            import time
            
            steps = [
                ("Loading training data...", 20),
                ("Preparing model architecture...", 40),
                ("Training model...", 70),
                ("Validating model...", 90),
                ("Saving model...", 100)
            ]
            
            for step_msg, progress in steps:
                if log_message_callback:
                    log_message_callback(step_msg)
                if progress_callback:
                    progress_callback(progress, 100, step_msg)
                time.sleep(1)  # Simulate work
            
            return {
                "success": True,
                "message": "Base model training completed successfully"
            }
            
        except Exception as e:
            if log_message_callback:
                log_message_callback(f"Error during base training: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _perform_finetuning_worker(self, progress_callback=None, log_message_callback=None):
        """Worker function for model finetuning."""
        try:
            if log_message_callback:
                log_message_callback("Initializing model finetuning...")
            
            if progress_callback:
                progress_callback(10, 100, "Loading feedback data...")
            
            # TODO: Implement actual finetuning logic
            # For now, simulate finetuning process
            import time
            
            steps = [
                ("Loading feedback data...", 20),
                ("Preparing training examples...", 40),
                ("Finetuning model...", 70),
                ("Evaluating improvements...", 90),
                ("Saving finetuned model...", 100)
            ]
            
            for step_msg, progress in steps:
                if log_message_callback:
                    log_message_callback(step_msg)
                if progress_callback:
                    progress_callback(progress, 100, step_msg)
                time.sleep(1)  # Simulate work
            
            return {
                "success": True,
                "message": "Model finetuning completed successfully"
            }
            
        except Exception as e:
            if log_message_callback:
                log_message_callback(f"Error during finetuning: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def on_model_source_changed(self, source: str):
        """Handle model source selection change."""
        w = self.widgets["ai_tab"]
        
        if source == "Ollama":
            w["ollama_model_label"].setVisible(True)
            w["ollama_model_selector"].setVisible(True)
            w["refresh_models_button"].setVisible(True)
            w["load_model_button"].setVisible(False)
            w["model_status_label"].setText("Status: Using Ollama")
            self.populate_ollama_models()
        else:  # Fine-tuned Local Model
            w["ollama_model_label"].setVisible(False)
            w["ollama_model_selector"].setVisible(False)
            w["refresh_models_button"].setVisible(False)
            w["load_model_button"].setVisible(True)
            w["model_status_label"].setText("Status: Ready to load fine-tuned model")
            self.update_model_info()

    def load_fine_tuned_model(self):
        """Load a fine-tuned local model."""
        try:
            w = self.widgets["ai_tab"]
            w["model_status_label"].setText("Status: Loading fine-tuned model...")
            
            # Get the local code reviewer
            reviewer = self.backend_controller.get_local_code_reviewer()
            model_info = reviewer.get_model_info()
            
            if model_info["is_fine_tuned"]:
                w["model_status_label"].setText(f"Status: Using {model_info['current_model']}")
                self.update_model_info()
                QMessageBox.information(self, "Success", f"Loaded fine-tuned model: {model_info['current_model']}")
            else:
                w["model_status_label"].setText("Status: No fine-tuned model available")
                QMessageBox.warning(self, "Warning", "No fine-tuned model found. Using default model.")
                
        except Exception as e:
            self.log_message(f"Error loading fine-tuned model: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load fine-tuned model: {e}")

    def update_model_info(self):
        """Update the model information display."""
        try:
            w = self.widgets["ai_tab"]
            reviewer = self.backend_controller.get_local_code_reviewer()
            model_info = reviewer.get_model_info()
            
            info_text = f"Current: {model_info['current_model']}"
            if model_info["is_fine_tuned"]:
                info_text += " (Fine-tuned)"
            else:
                info_text += " (Base model)"
            
            w["model_info_label"].setText(info_text)
            
        except Exception as e:
            self.log_message(f"Error updating model info: {e}")

    def on_issue_double_clicked(self, row: int, column: int):
        """Handle double-click on an issue in the results table."""
        try:
            w = self.widgets["ai_tab"]
            table = w["results_table"]
            
            # Get the issue data from the first column
            file_item = table.item(row, 0)
            if file_item:
                issue_data = file_item.data(Qt.ItemDataRole.UserRole)
                if issue_data:
                    self.enhance_issue_with_ai(issue_data)
                    
        except Exception as e:
            self.log_message(f"Error handling issue double-click: {e}")

    def export_scan_results(self):
        """Export scan results to a file."""
        try:
            w = self.widgets["ai_tab"]
            table = w["results_table"]
            
            if table.rowCount() == 0:
                QMessageBox.information(self, "No Results", "No results to export.")
                return
            
            # Get save file path with all format options
            file_path, selected_filter = QFileDialog.getSaveFileName(
                self, 
                "Export Scan Results", 
                "", 
                "JSON Files (*.json);;CSV Files (*.csv);;Markdown Files (*.md);;HTML Files (*.html);;PDF Files (*.pdf)"
            )
            
            if file_path:
                # Collect all issues
                issues = []
                for row in range(table.rowCount()):
                    file_item = table.item(row, 0)
                    if file_item:
                        issue_data = file_item.data(Qt.ItemDataRole.UserRole)
                        if issue_data:
                            issues.append(issue_data)
                
                # Prepare report data
                report_data = {
                    "scan_date": datetime.now().isoformat(),
                    "total_issues": len(issues),
                    "issues": issues
                }
                
                # Export based on file extension or selected filter
                if file_path.endswith('.json') or "JSON" in selected_filter:
                    with open(file_path, 'w') as f:
                        json.dump(report_data, f, indent=2)
                elif file_path.endswith('.csv') or "CSV" in selected_filter:
                    import csv
                    with open(file_path, 'w', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow(['File', 'Line', 'Type', 'Severity', 'Issue'])
                        for issue in issues:
                            writer.writerow([
                                issue.get('file', ''),
                                issue.get('line', ''),
                                issue.get('type', ''),
                                issue.get('severity', ''),
                                issue.get('issue', '')
                            ])
                elif file_path.endswith('.md') or "Markdown" in selected_filter:
                    # Use the intelligent analyzer's markdown export
                    from src.backend.services.intelligent_analyzer import export_report
                    export_report(report_data, "Markdown (.md)", file_path)
                elif file_path.endswith('.html') or "HTML" in selected_filter:
                    # Convert to HTML using markdown
                    from src.backend.services.intelligent_analyzer import generate_markdown_string
                    import markdown
                    md_content = generate_markdown_string(report_data)
                    html_content = markdown.markdown(md_content)
                    
                    # Add basic HTML styling
                    full_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>AI Code Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #666; margin-top: 30px; }}
        h3 {{ color: #888; }}
        code {{ background-color: #f4f4f4; padding: 2px 4px; border-radius: 3px; }}
        pre {{ background-color: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }}
        .issue {{ border-left: 4px solid #007acc; padding-left: 15px; margin: 20px 0; }}
        .severity-high {{ border-left-color: #d73a49; }}
        .severity-medium {{ border-left-color: #f6a434; }}
        .severity-low {{ border-left-color: #28a745; }}
    </style>
</head>
<body>
{html_content}
</body>
</html>
"""
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(full_html)
                elif file_path.endswith('.pdf') or "PDF" in selected_filter:
                    # Use the intelligent analyzer's PDF export
                    from src.backend.services.intelligent_analyzer import export_report
                    export_report(report_data, "PDF", file_path)
                
                QMessageBox.information(self, "Success", f"Results exported to: {file_path}")
                
        except Exception as e:
            self.log_message(f"Error exporting results: {e}")
            QMessageBox.critical(self, "Error", f"Failed to export results: {e}")
