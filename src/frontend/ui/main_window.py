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
from src.frontend.ui.advanced_analytics_tab import AdvancedAnalyticsTab
from src.frontend.ui.cloud_models_tab import CloudModelsTab
from src.frontend.ui.code_standards_tab import CodeStandardsTab
from src.frontend.ui.collaboration_tab import CollaborationTab
from src.frontend.ui.continuous_learning_tab import ContinuousLearningTab
from src.frontend.ui.data_tab_widgets import setup_data_tab
from src.frontend.ui.ollama_export_tab import setup_ollama_export_tab
from src.frontend.ui.ollama_manager_tab import LLMManager, OllamaManagerTab
from src.frontend.ui.performance_optimization_tab import PerformanceOptimizationTab
from src.frontend.ui.pr_tab_widgets import setup_pr_tab
from src.frontend.ui.refactoring_tab import RefactoringTab
from src.frontend.ui.security_intelligence_tab import SecurityIntelligenceTab
from src.frontend.ui.suggestion_dialog import SuggestionDialog
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
        self.setup_ollama_manager_tab()
        self.setup_ollama_export_tab()
        self.setup_continuous_learning_tab()
        self.setup_code_standards_tab()
        self.setup_security_intelligence_tab()
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

        # Create buttons layout
        buttons_layout = QHBoxLayout()
        main_layout.addLayout(buttons_layout)

        self.create_report_button = QPushButton("Create Report")
        self.create_report_button.setEnabled(False)
        self.create_report_button.clicked.connect(self.start_report_generation)
        buttons_layout.addWidget(self.create_report_button)

        self.enhance_button = QPushButton("Enhance with AI")
        self.enhance_button.setEnabled(False)
        self.enhance_button.clicked.connect(self.start_ai_enhancement)
        buttons_layout.addWidget(self.enhance_button)

        self.review_suggestions_button = QPushButton("Review Suggestions")
        self.review_suggestions_button.setEnabled(False)
        buttons_layout.addWidget(self.review_suggestions_button)

    def setup_ai_tab(self):
        """Set up the AI tab."""
        ai_tab = QWidget()
        main_layout = QVBoxLayout(ai_tab)

        # Create a dictionary to hold all AI tab widgets
        if not hasattr(self, "widgets"):
            self.widgets = {}
        self.widgets["ai_tab"] = {}
        w = self.widgets["ai_tab"]

        # 1. AI Model Configuration
        model_group = QGroupBox("1. AI Model Configuration")
        model_layout = QGridLayout()
        model_group.setLayout(model_layout)
        main_layout.addWidget(model_group)

        model_layout.addWidget(QLabel("Model Source:"), 0, 0)
        w["model_source_selector"] = QComboBox()
        w["model_source_selector"].addItems(
            ["Ollama", "Own Model", "OpenAI", "Google Gemini", "Claude"]
        )
        model_layout.addWidget(w["model_source_selector"], 0, 1)

        model_layout.addWidget(QLabel("Ollama Model:"), 1, 0)
        w["ollama_model_selector"] = QComboBox()
        model_layout.addWidget(w["ollama_model_selector"], 1, 1)

        w["refresh_models_button"] = QPushButton("Refresh Models")
        model_layout.addWidget(w["refresh_models_button"], 1, 2)

        model_layout.addWidget(QLabel("Own Model Status:"), 2, 0)
        w["own_model_status_label"] = QLabel("Not Loaded")
        model_layout.addWidget(w["own_model_status_label"], 2, 1)

        w["load_model_button"] = QPushButton("Load Trained Model")
        model_layout.addWidget(w["load_model_button"], 2, 2)

        # 2. Code Scanning
        scan_group = QGroupBox("2. Code Scanning")
        scan_layout = QGridLayout()
        scan_group.setLayout(scan_layout)
        main_layout.addWidget(scan_group)

        scan_layout.addWidget(QLabel("Include Patterns:"), 0, 0)
        w["include_patterns_edit"] = QLineEdit("*.py,*.js,*.java,*.cpp,*.c,*.h")
        scan_layout.addWidget(w["include_patterns_edit"], 0, 1)

        scan_layout.addWidget(QLabel("Exclude Patterns:"), 1, 0)
        w["exclude_patterns_edit"] = QLineEdit(
            "*/.venv/*,*/node_modules/*,*/tests/*,*.md"
        )
        scan_layout.addWidget(w["exclude_patterns_edit"], 1, 1)

        w["enable_ai_analysis_checkbox"] = QCheckBox("Enable AI-Powered Analysis")
        w["enable_ai_analysis_checkbox"].setChecked(True)
        scan_layout.addWidget(w["enable_ai_analysis_checkbox"], 2, 0)

        scan_layout.addWidget(QLabel("Project Directory:"), 3, 0)
        w["project_dir_edit"] = QLineEdit(os.getcwd())
        scan_layout.addWidget(w["project_dir_edit"], 3, 1)

        w["browse_button"] = QPushButton("Browse...")
        scan_layout.addWidget(w["browse_button"], 3, 2)

        w["start_scan_button"] = QPushButton("Start Scan")
        scan_layout.addWidget(w["start_scan_button"], 4, 0, 1, 3)

        w["stop_scan_button"] = QPushButton("Stop Scan")
        w["stop_scan_button"].setEnabled(False)
        w["stop_scan_button"].clicked.connect(self.stop_scan)
        scan_layout.addWidget(w["stop_scan_button"], 5, 0, 1, 3)

        # 3. Results/Suggestions
        results_group = QGroupBox("3. Results/Suggestions")
        results_layout = QVBoxLayout()
        results_group.setLayout(results_layout)
        main_layout.addWidget(results_group)

        w["scan_results_text"] = QTextEdit()
        w["scan_results_text"].setReadOnly(True)
        results_layout.addWidget(w["scan_results_text"])

        # Create buttons layout
        buttons_layout = QHBoxLayout()
        results_layout.addLayout(buttons_layout)

        w["create_report_button"] = QPushButton("Create Report")
        w["create_report_button"].setEnabled(False)
        buttons_layout.addWidget(w["create_report_button"])

        w["enhance_button"] = QPushButton("Enhance with AI")
        w["enhance_button"].setEnabled(False)
        buttons_layout.addWidget(w["enhance_button"])

        w["review_suggestions_button"] = QPushButton("Review Suggestions")
        w["review_suggestions_button"].setEnabled(False)
        buttons_layout.addWidget(w["review_suggestions_button"])

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

    def setup_ollama_manager_tab(self):
        """Set up the Ollama manager tab."""
        llm_manager = LLMManager()
        ollama_manager_tab = OllamaManagerTab(llm_manager)
        self.tab_widget.addTab(ollama_manager_tab, "Ollama Manager")

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
            w = self.widgets["ai_tab"]
            w["refresh_models_button"].clicked.connect(self.populate_ollama_models)
            w["load_model_button"].clicked.connect(self.load_trained_model)
            w["browse_button"].clicked.connect(self.select_scan_directory)
            w["start_scan_button"].clicked.connect(self.start_scan)
            w["create_report_button"].clicked.connect(self.start_report_generation)
            w["enhance_button"].clicked.connect(self.start_ai_enhancement)
            w["review_suggestions_button"].clicked.connect(self.review_next_suggestion)
            w["model_source_selector"].currentTextChanged.connect(
                self._on_model_source_changed
            )
            w["ollama_model_selector"].currentTextChanged.connect(
                self._on_ollama_model_selected
            )
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
        directory = QFileDialog.getExistingDirectory(self, "Select Directory to Scan")
        if directory:
            self.scan_directory = directory
            # Update the appropriate directory field based on which tab is active
            if hasattr(self, "project_dir_edit"):
                self.widgets["ai_tab"]["project_dir_edit"].setText(directory)
            if hasattr(self, "scan_dir_entry"):
                self.scan_dir_entry.setText(directory)
            self.log_message(f"Selected scan directory: {directory}")

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
            # Validate that we have suggestions to report
            if not hasattr(self, "suggestion_list") or not self.suggestion_list:
                QMessageBox.warning(
                    self,
                    "No Data for Report",
                    "Please run a scan first to generate data for the report.",
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
            self.log_message("Starting report generation...")
            w["create_report_button"].setEnabled(
                False
            )  # Disable button during generation

            self.start_worker(
                "generate_report",
                ai_tools.generate_report_and_training_data,
                self.suggestion_list,
                model_mode,
                model_ref,
                tokenizer_ref,
                progress_callback=self.update_report_progress,
                log_message_callback=self.log_message,
            )

        except Exception as e:
            self.log_message(f"Error starting report generation: {e}")
            QMessageBox.critical(
                self,
                "Report Generation Error",
                f"Failed to start report generation:\n{str(e)}\n\nPlease check the logs for more details.",
            )
            w["create_report_button"].setEnabled(True)
            if hasattr(self, "report_progress_dialog") and self.report_progress_dialog:
                self.report_progress_dialog.close()

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
            w["start_scan_button"].setEnabled(True)
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
            self.log_message(f"Error stopping scan: {e}", "error")

    def start_scan(self):
        w = self.widgets["ai_tab"]
        w["scan_results_text"].setPlainText("Starting code scan...")
        w["create_report_button"].setEnabled(False)
        w["enhance_button"].setEnabled(False)
        w["review_suggestions_button"].setEnabled(False)

        # Disable start button and enable stop button
        w["start_scan_button"].setEnabled(False)
        w["stop_scan_button"].setEnabled(True)

        self.scan_directory = w["project_dir_edit"].text()
        if not os.path.exists(self.scan_directory):
            QMessageBox.warning(
                self,
                "Invalid Directory",
                f"The directory '{self.scan_directory}' does not exist.",
            )
            # Re-enable start button and disable stop button
            w["start_scan_button"].setEnabled(True)
            w["stop_scan_button"].setEnabled(False)
            return

        # Create progress dialog
        self.progress_dialog = QProgressDialog(
            "Scanning code...", "Cancel", 0, 100, self
        )
        self.progress_dialog.setWindowTitle("Code Scan Progress")
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
        enable_ai_powered = w["enable_ai_analysis_checkbox"].isChecked()

        # Use the new ScannerService
        def scan_callback(result):
            """Callback for scan completion"""
            if result:
                # Convert scanner service result to the expected format
                scan_results = []
                for file_path, file_result in result.get("results", {}).items():
                    if file_result and file_result.get("issues"):
                        scan_results.append(
                            {
                                "file_path": file_path,
                                "language": file_result.get("language", "unknown"),
                                "issues": file_result.get("issues", []),
                                "suggestions": [],
                            }
                        )
                return scan_results
            return []

        # Start scan using the scanner service
        scan_id = self.scanner_service.start_scan(
            directory=self.scan_directory,
            model_name=self.current_model_ref if enable_ai_powered else None,
            callback=scan_callback,
        )

        # Store the scan ID for cancellation
        self.current_worker_id = scan_id
        self.current_scan_future = None  # Scanner service handles its own threading

        # Set up a timer to check scan status
        self.scan_status_timer = QTimer()
        self.scan_status_timer.timeout.connect(self._check_scan_status)
        self.scan_status_timer.start(1000)  # Check every second

    def _check_scan_status(self):
        """Check the status of the current scan and update progress."""
        if not self.current_worker_id:
            return

        try:
            status = self.scanner_service.get_scan_status()
            if status is None:
                # Scan completed or failed
                self.scan_status_timer.stop()
                self._handle_scan_completion()
                return

            # Update progress based on status
            if status == TaskStatus.IN_PROGRESS:
                if self.progress_dialog:
                    self.progress_dialog.setValue(50)  # Indeterminate progress
                    self.progress_dialog.setLabelText("Scanning files...")
            elif status == TaskStatus.COMPLETED:
                self.scan_status_timer.stop()
                self._handle_scan_completion()
            elif status == TaskStatus.FAILED:
                self.scan_status_timer.stop()
                self.log_message("Scan failed", "error")
                self._handle_scan_completion()
            elif status == TaskStatus.CANCELLED:
                self.scan_status_timer.stop()
                self.log_message("Scan cancelled", "info")
                self._handle_scan_completion()

        except Exception as e:
            self.log_message(f"Error checking scan status: {e}", "error")
            self.scan_status_timer.stop()
            self._handle_scan_completion()

    def _handle_scan_completion(self):
        """Handle scan completion and update UI."""
        try:
            # Get scan result
            if self.current_worker_id:
                scan_result = self.scanner_service.get_scan_result(
                    self.current_worker_id
                )
                if scan_result and scan_result.status == ScanStatus.COMPLETED:
                    # Convert to expected format
                    result_data = (
                        scan_result.result_data
                        if hasattr(scan_result, "result_data")
                        else {}
                    )
                    scan_results = []
                    for file_path, file_result in result_data.get(
                        "results", {}
                    ).items():
                        if file_result and file_result.get("issues"):
                            scan_results.append(
                                {
                                    "file_path": file_path,
                                    "language": file_result.get("language", "unknown"),
                                    "issues": file_result.get("issues", []),
                                    "suggestions": [],
                                }
                            )
                    self._handle_scan_complete_ui(scan_results)
                else:
                    self._handle_scan_complete_ui([])
            else:
                self._handle_scan_complete_ui([])
        except Exception as e:
            self.log_message(f"Error handling scan completion: {e}", "error")
            self._handle_scan_complete_ui([])
        finally:
            # Clear scan state
            self.current_worker_id = None
            self.current_scan_future = None

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

    def handle_scan_complete(self, future):
        """
        Callback for when a scan is complete. Emits a signal to update the UI
        on the main thread. This method is called from the background thread.
        """
        try:
            # Clear the scan state
            self.current_worker_id = None
            self.current_scan_future = None

            # Extract result from future
            if future.cancelled():
                self.log_message("Scan was cancelled.")
                result = []
            else:
                result = future.result() or []

            self.scan_completed.emit(result)
            self.log_message("Scan complete.")
            self._handle_scan_complete_ui(result)

        except Exception as e:
            self.log_message(f"Error in scan completion: {e}", "error")
            # Clear scan state on error
            self.current_worker_id = None
            self.current_scan_future = None
            # Emit empty result to reset UI
            self.scan_completed.emit([])
            self._handle_scan_complete_ui([])

    @pyqtSlot(list)
    def _handle_scan_complete_ui(self, result):
        """Update the UI with scan results, running in the main thread."""
        try:
            self.scan_results = result  # Store results
            formatted_text = self.format_issues_for_display(result)
            self.widgets["ai_tab"]["scan_results_text"].setText(formatted_text)
            self.log_message(
                f"Scan finished. Displaying {len(result)} files with issues."
            )
        except Exception as e:
            self.log_message(f"Error displaying scan results: {e}", "error")
        finally:
            # Reset scan button states
            w = self.widgets["ai_tab"]
            w["start_scan_button"].setEnabled(True)
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

    def _enable_post_scan_buttons(self, enabled: bool):
        """Enable or disable buttons that require scan results."""
        self.widgets["ai_tab"]["create_report_button"].setEnabled(enabled)
        self.widgets["ai_tab"]["enhance_button"].setEnabled(enabled)
        self.widgets["ai_tab"]["review_suggestions_button"].setEnabled(enabled)

    def show_suggestion_dialog(self, suggestion: Dict[str, Any], ai_explanation: str):
        dialog = SuggestionDialog(suggestion, ai_explanation, self)
        result = dialog.exec()

        if result == SuggestionDialog.ApplyCode:
            # Apply the suggestion
            self.apply_suggestion(suggestion)
            self.current_suggestion_index += 1
            self.review_next_suggestion()
        elif result == SuggestionDialog.CancelCode:
            # Skip this suggestion
            self.current_suggestion_index += 1
            self.review_next_suggestion()
        elif result == SuggestionDialog.CancelAllCode:
            # Cancel the entire review process
            self.current_suggestion_index = len(self.suggestion_list)
            QMessageBox.information(
                self, "Review Cancelled", "Code review process cancelled."
            )

        # Store user feedback if provided
        user_feedback = dialog.get_user_justification()
        if user_feedback:
            self.log_message(
                f"User feedback for suggestion {self.current_suggestion_index}: {user_feedback}"
            )

    def refresh_ollama_models(self):
        """Refresh the list of available Ollama models."""
        try:
            from backend.services.ollama_client import get_available_models_sync

            # Get available models
            models = get_available_models_sync()

            if not models:
                self.log_message(
                    "No Ollama models found. Please ensure Ollama is running and models are installed."
                )
                return

            # Update model selector
            if hasattr(self, "widgets"):
                current_model = self.widgets["ai_tab"][
                    "ollama_model_selector"
                ].currentText()
                self.widgets["ai_tab"]["ollama_model_selector"].clear()
                self.widgets["ai_tab"]["ollama_model_selector"].addItems(models)

                # Try to restore previous selection if it still exists
                if current_model in models:
                    self.widgets["ai_tab"]["ollama_model_selector"].setCurrentText(
                        current_model
                    )
                elif models:
                    # Select first available model
                    self.widgets["ai_tab"]["ollama_model_selector"].setCurrentText(
                        models[0]
                    )

                self.log_message(f"Found {len(models)} Ollama models")
        except Exception as e:
            self.log_message(f"Error refreshing Ollama models: {str(e)}")
            QMessageBox.warning(
                self, "Refresh Error", f"Failed to refresh Ollama models: {str(e)}"
            )

    def start_ai_enhancement(self):
        """Starts AI enhancement of scan results in a background thread."""
        model_name = self.widgets["ai_tab"]["ollama_model_selector"].currentText()
        if not model_name:
            QMessageBox.warning(
                self, "Model Not Selected", "Please select an Ollama model first."
            )
            return

        if not self.scan_results:
            QMessageBox.warning(
                self,
                "No Results",
                "Please run a scan first to generate results to enhance.",
            )
            return

        self._enable_post_scan_buttons(False)

        self.progress_dialog = QProgressDialog(
            "Enhancing with AI...", "Cancel", 0, len(self.scan_results), self
        )
        self.progress_dialog.setWindowTitle("AI Enhancement Progress")
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.show()

        future = self.executor.submit(
            scanner.enhance_issues_with_ai,
            self.scan_results,
            model_name,
            progress_callback=self.scan_progress_updated.emit,
        )
        future.add_done_callback(self.handle_enhancement_complete)
        self.progress_dialog.canceled.connect(future.cancel)

    def handle_enhancement_complete(self, future):
        """Callback for when AI enhancement is complete."""
        try:
            if future.cancelled():
                self.log_message("AI enhancement was cancelled.", "warning")
                # Don't overwrite results if cancelled
                QTimer.singleShot(0, lambda: self._enable_post_scan_buttons(True))
            else:
                enhanced_results = future.result()
                if enhanced_results is not None:
                    # Update UI on the main thread
                    QTimer.singleShot(
                        0, lambda: self._handle_scan_complete_ui(enhanced_results)
                    )
                else:
                    self.log_message("AI enhancement failed. Check logs.", "error")
                    QTimer.singleShot(0, lambda: self._enable_post_scan_buttons(True))
        except Exception as e:
            self.log_message(f"AI enhancement failed: {e}", "error")
            QTimer.singleShot(0, lambda: self._enable_post_scan_buttons(True))
        finally:
            if self.progress_dialog is not None:
                try:
                    QTimer.singleShot(0, self.progress_dialog.close)
                except Exception as e:
                    self.log_message(f"Error closing progress dialog: {e}", "error")
                finally:
                    self.progress_dialog = None

    def format_issues_for_display(self, result: List[Dict[str, Any]]) -> str:
        """Formats the scan results for display in the QTextEdit."""
        if not result:
            return "No issues found."

        output_lines = []
        for file_result in result:
            file_path = file_result.get("file_path", "N/A")
            issues = file_result.get("issues", [])
            if not issues:
                continue

            output_lines.append(f"--- {file_path} ({len(issues)} issues) ---")
            for issue in issues:
                line = issue.get("line", "N/A")
                desc = issue.get("description", "No description.")
                suggestion = issue.get("suggestion")

                output_lines.append(f"  Line {line}: {desc}")
                if suggestion:
                    output_lines.append(f"    └ Suggestion: {suggestion}")
            output_lines.append("")

        return "\n".join(output_lines)

    def update_preprocess_progress(self, current: int, total: int, message: str):
        """Update preprocessing progress with proper error handling."""
        try:
            if self.progress_dialog is not None:
                self.progress_dialog.setRange(0, total)
                self.progress_dialog.setValue(current)
                self.progress_dialog.setLabelText(
                    f"{message}\\nProgress: {current}/{total}"
                )
                if current >= total:
                    self.progress_dialog.setValue(total)
        except Exception as e:
            self.log_message(f"Error updating preprocess progress: {e}")
            # Clean up the dialog if it's in an invalid state
            self.progress_dialog = None

    def start_base_training(self):
        """Start base model training with proper error handling."""
        try:
            self.progress_dialog = QProgressDialog(
                "Training Base Model...",
                "Cancel",
                PROGRESS_DIALOG_MIN_VALUE,
                PROGRESS_DIALOG_MAX_VALUE,
                self,
            )
            self.progress_dialog.setWindowTitle("Training Progress")
            self.progress_dialog.setAutoClose(True)
            self.progress_dialog.setAutoReset(True)
            self.progress_dialog.setMinimumDuration(0)
            self.progress_dialog.setValue(0)
            self.progress_dialog.show()
            self.start_worker(
                "train_base",
                trainer.train_base_model,
                progress_callback=self.update_training_progress,
            )
        except Exception as e:
            self.log_message(f"Error starting training: {e}")
            QMessageBox.critical(
                self, "Training Error", f"Failed to start training: {str(e)}"
            )

    def update_training_progress(self, current: int, total: int, message: str):
        """Update training progress with proper error handling."""
        try:
            if self.progress_dialog is not None:
                self.progress_dialog.setRange(
                    PROGRESS_DIALOG_MIN_VALUE, PROGRESS_DIALOG_MAX_VALUE
                )
                self.progress_dialog.setValue(current)
                self.progress_dialog.setLabelText(
                    f"{message}\\nProgress: {current}/{total}"
                )
                if current >= total:
                    self.progress_dialog.setValue(total)
        except Exception as e:
            self.log_message(f"Error updating training progress: {e}")
            # Clean up the dialog if it's in an invalid state
            self.progress_dialog = None

    def start_finetuning(self):
        """Start model finetuning with proper error handling."""
        try:
            self.progress_dialog = QProgressDialog(
                "Finetuning Model...",
                "Cancel",
                PROGRESS_DIALOG_MIN_VALUE,
                PROGRESS_DIALOG_MAX_VALUE,
                self,
            )
            self.progress_dialog.setWindowTitle("Finetuning Progress")
            self.progress_dialog.setAutoClose(True)
            self.progress_dialog.setAutoReset(True)
            self.progress_dialog.setMinimumDuration(0)
            self.progress_dialog.setValue(0)
            self.progress_dialog.show()
            self.start_worker(
                "finetune",
                trainer.finetune_model,
                progress_callback=self.update_finetune_progress,
            )
        except Exception as e:
            self.log_message(f"Error starting finetuning: {e}")
            QMessageBox.critical(
                self, "Finetuning Error", f"Failed to start finetuning: {str(e)}"
            )

    def update_finetune_progress(self, current: int, total: int, message: str):
        """Update finetuning progress with proper error handling."""
        try:
            if self.progress_dialog is not None:
                self.progress_dialog.setRange(
                    PROGRESS_DIALOG_MIN_VALUE, PROGRESS_DIALOG_MAX_VALUE
                )
                self.progress_dialog.setValue(current)
                self.progress_dialog.setLabelText(
                    f"{message}\\nProgress: {current}/{total}"
                )
                if current >= total:
                    self.progress_dialog.setValue(total)
        except Exception as e:
            self.log_message(f"Error updating finetune progress: {e}")
            # Clean up the dialog if it's in an invalid state
            self.progress_dialog = None

    def update_generic_progress(self, current: int, total: int, message: str):
        """Generic progress update handler for tasks without specific progress dialogs."""
        try:
            if self.progress_dialog is not None:
                self.progress_dialog.setRange(0, total)
                self.progress_dialog.setValue(current)
                self.progress_dialog.setLabelText(
                    f"{message}\\nProgress: {current}/{total}"
                )
                if current >= total:
                    self.progress_dialog.setValue(total)
        except Exception as e:
            self.log_message(f"Error updating generic progress: {e}")
            # Clean up the dialog if it's in an invalid state
            self.progress_dialog = None

    def update_docker_status(self):
        """Update Docker status with proper error handling."""
        try:
            if is_docker_available():
                self.docker_status_label.setText("Docker detected ✔️")
                self.docker_enable_checkbox.setEnabled(True)
            else:
                self.docker_status_label.setText("Docker not found ✖️")
                self.docker_enable_checkbox.setEnabled(False)
                self.docker_enable_checkbox.setChecked(False)
        except Exception as e:
            self.log_message(f"Error updating Docker status: {e}")

    def on_docker_checkbox_changed(self, state):
        """Handle Docker checkbox changes with proper error handling."""
        try:
            if state == Qt.CheckState.Checked.value:
                self.log_message("Docker integration enabled.")
            else:
                self.log_message("Docker integration disabled.")
        except Exception as e:
            self.log_message(f"Error handling Docker checkbox change: {e}")

    def browse_dockerfile(self):
        """Browse for Dockerfile with proper error handling."""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select Dockerfile", "", "Dockerfile (*)"
            )
            if file_path:
                self.dockerfile_path_edit.setText(file_path)
        except Exception as e:
            self.log_message(f"Error browsing Dockerfile: {e}")
            QMessageBox.warning(self, "Error", f"Failed to browse Dockerfile: {str(e)}")

    def on_test_docker_btn_clicked(self):
        """Test Docker functionality with proper error handling."""
        try:
            print("[DEBUG] Entered on_test_docker_btn_clicked")
            # Gather settings from GUI
            context_dir = os.getcwd()
            dockerfile_path = self.dockerfile_path_edit.text().strip() or None
            build_args = self.build_args_edit.text().strip()
            run_opts = self.run_opts_edit.text().strip()
            print(
                f"[DEBUG] context_dir={context_dir}, dockerfile_path={dockerfile_path}, build_args={build_args}, run_opts={run_opts}"
            )
            # Call backend logic
            print("[DEBUG] About to call run_build_and_test_in_docker")
            result = run_build_and_test_in_docker(
                context_dir=context_dir,
                dockerfile_path=dockerfile_path,
                build_args=build_args,
                run_opts=run_opts,
                test_command="python run_tests.py",
            )
            print("[DEBUG] run_build_and_test_in_docker returned")
            # Show result to user
            if result.get("success"):
                QMessageBox.information(
                    self,
                    "Docker Build/Test Success",
                    f"Stage: {result.get('stage')}\\nOutput:\\n{result.get('output')}",
                )
            else:
                QMessageBox.critical(
                    self,
                    "Docker Build/Test Failed",
                    f"Stage: {result.get('stage', 'unknown')}\\nError:\\n{result.get('output', result.get('error', 'Unknown error'))}",
                )
        except Exception as e:
            self.log_message(f"Error testing Docker: {e}")
            QMessageBox.critical(
                self, "Docker Test Error", f"Failed to test Docker: {str(e)}"
            )

    def start_worker(self, worker_id: str, target_func, *args, **kwargs):
        """Start a background task using ThreadPoolExecutor."""
        try:
            original_callback = kwargs.pop("callback", None)

            def cleanup_callback(future):
                result = None
                try:
                    result = future.result()
                except Exception as e:
                    # Log error in the main thread, capturing the exception's value
                    QTimer.singleShot(
                        0,
                        lambda err=e: self.log_message(
                            f"Error in worker {worker_id}: {err}"
                        ),
                    )

                if original_callback:
                    # Ensure original callback also runs in the main thread
                    QTimer.singleShot(0, lambda: original_callback(result))

                # Update active workers list in the main thread
                QTimer.singleShot(
                    0,
                    lambda: (
                        self.active_workers.remove(worker_id)
                        if worker_id in self.active_workers
                        else None
                    ),
                )

            future = self.executor.submit(target_func, *args, **kwargs)
            self.active_workers.append(worker_id)
            future.add_done_callback(cleanup_callback)
        except Exception as e:
            self.log_message(f"Error starting worker {worker_id}: {e}")
            if self.progress_dialog is not None:
                try:
                    self.progress_dialog.close()
                except Exception as close_error:
                    self.log_message(
                        f"Error closing progress dialog: {close_error}", "error"
                    )
                finally:
                    self.progress_dialog = None
            raise
