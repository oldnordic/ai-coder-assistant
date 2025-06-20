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

# src/frontend/ui/main_window.py
import os
import logging
import time
from PyQt6.QtWidgets import (QMainWindow, QTabWidget, QApplication, QWidget,
                             QPushButton, QMessageBox, QFileDialog, QProgressDialog,
                             QTextEdit, QVBoxLayout, QLabel, QHBoxLayout, QGroupBox, QCheckBox, QLineEdit, QComboBox, QSpinBox, QGridLayout)
from PyQt6.QtCore import QUrl, pyqtSlot, Qt, QTimer, QMutex, QMutexLocker, pyqtSignal

from frontend.controllers.backend_controller import BackendController
from frontend.ui.data_tab_widgets import setup_data_tab
from frontend.ui.ollama_manager_tab import OllamaManagerTab, LLMManager
from frontend.ui.ollama_export_tab import setup_ollama_export_tab
from frontend.ui.pr_tab_widgets import setup_pr_tab
from frontend.ui.code_standards_tab import CodeStandardsTab
from frontend.ui.continuous_learning_tab import ContinuousLearningTab
from frontend.ui.refactoring_tab import RefactoringTab
from frontend.ui.security_intelligence_tab import SecurityIntelligenceTab
from frontend.ui.performance_optimization_tab import PerformanceOptimizationTab
from frontend.ui.advanced_analytics_tab import AdvancedAnalyticsTab
from frontend.ui.web_server_tab import WebServerTab
from frontend.ui.collaboration_tab import CollaborationTab
from frontend.ui.cloud_models_tab import CloudModelsTab
from backend.utils import settings

from backend.services import ai_tools, scanner, get_available_models_sync
from backend.services import acquire, preprocess
from backend.services import trainer
from backend.utils.constants import (
    PROGRESS_DIALOG_MAX_VALUE, PROGRESS_DIALOG_MIN_VALUE,
    MAIN_WINDOW_MIN_WIDTH, MAIN_WINDOW_MIN_HEIGHT,
    LOG_OUTPUT_MAX_HEIGHT, DOC_URLS_INPUT_MAX_HEIGHT,
    LOG_QUEUE_PROCESS_INTERVAL_MS,
    DEFAULT_MAX_PAGES_SPINBOX_VALUE, DEFAULT_MAX_DEPTH_SPINBOX_VALUE,
    MAX_PAGES_SPINBOX_RANGE, MAX_DEPTH_SPINBOX_RANGE
)

from backend.utils.settings import is_docker_available
from backend.services.docker_utils import run_build_and_test_in_docker
from backend.services.llm_manager import LLMManager
from frontend.ui.suggestion_dialog import SuggestionDialog
from typing import Dict, Any, Optional, List
import concurrent.futures


# Set up a logger for this module
logger = logging.getLogger(__name__)

class AICoderAssistant(QMainWindow):
    # --- Signals for thread-safe UI updates ---
    scan_progress_updated = pyqtSignal(int, int, str)
    scan_completed = pyqtSignal(list)
    # ---

    def __init__(self):
        super().__init__()
        self.active_workers = []
        self.progress_dialog = None
        self.report_progress_dialog = None
        self.current_model_ref = None  # Initialize model reference
        self.current_tokenizer_ref = None  # Initialize tokenizer reference
        self.scan_directory = None
        self.executor = concurrent.futures.ThreadPoolExecutor()
        # Create backend controller
        self.backend_controller = BackendController()
        # Remove thread_manager and related logic
        # Initialize thread-safe logging
        self._log_mutex = QMutex()
        self._log_queue = []
        self._log_timer = QTimer()
        self._log_timer.timeout.connect(self._process_log_queue)
        self._log_timer.start(LOG_QUEUE_PROCESS_INTERVAL_MS)  # Process log queue every 50ms
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
        self.log_message("Main Window Initialized Successfully.")

        # Connect signals to their slots for thread-safe UI updates
        self.scan_progress_updated.connect(self._update_scan_progress_safe)
        self.scan_completed.connect(self._handle_scan_complete_ui)
    
    def start_doc_acquisition(self):
        """Start document acquisition from URLs."""
        urls = self.doc_urls_input.toPlainText().strip().split('\n')
        urls = [url.strip() for url in urls if url.strip()]
        if not urls:
            QMessageBox.warning(self, "Input Missing", "Please provide at least one URL.")
            return
        
        # Get scraping mode and parameters
        scraping_mode = self.scraping_mode_selector.currentText()
        max_pages = self.max_pages_spinbox.value()
        max_depth = self.max_depth_spinbox.value()
        same_domain_only = self.same_domain_checkbox.isChecked()
        
        # Ensure docs directory exists
        os.makedirs(settings.DOCS_DIR, exist_ok=True)
        
        self.log_message(f"Starting {scraping_mode.lower()} acquisition from {len(urls)} URLs...")
        self.log_message(f"Parameters: max_pages={max_pages}, max_depth={max_depth}, same_domain_only={same_domain_only}")
        
        # Update UI state
        self.start_acquisition_button.setEnabled(False)
        self.stop_scraping_button.setEnabled(True)
        
        # Create progress dialog
        self.progress_dialog = QProgressDialog("Initializing web scraping...", "Cancel", 0, len(urls), self)
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
                
                success_count = result.get('success_count', 0)
                total = result.get('total', 0)
                files = result.get('files', [])
                errors = result.get('errors', [])
                
                # Show results dialog
                message = "Web Scraping Complete\n\n"
                message += f"Successfully scraped {success_count} out of {total} URLs.\n\n"
                
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
            'max_pages': max_pages,
            'max_depth': max_depth,
            'same_domain_only': same_domain_only,
            'log_message_callback': self.log_message,
            'cancellation_callback': lambda: self.progress_dialog and self.progress_dialog.wasCanceled()
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
                    **params
                )
            else:  # Simple mode
                self.start_worker(
                    worker_id,
                    acquire.crawl_docs_simple,
                    urls,
                    settings.DOCS_DIR,  # Use the constant from settings
                    callback=completion_callback,
                    **params
                )
            
            # Connect progress dialog cancel button
            self.progress_dialog.canceled.connect(lambda: self.cancel_doc_acquisition(worker_id))
            
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
                    self.log_message(f"Error updating progress dialog during cancellation: {e}", "error")
            
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
        file_menu = menubar.addMenu('&File')
        
        # LLM Studio action
        llm_studio_action = file_menu.addAction('Open LLM Studio')
        llm_studio_action.triggered.connect(self.open_llm_studio)
        
        # Exit action
        exit_action = file_menu.addAction('Exit')
        exit_action.triggered.connect(self.close)
        
        # Help menu
        help_menu = menubar.addMenu('&Help')
        about_action = help_menu.addAction('About')
        about_action.triggered.connect(self.show_about)
    
    def open_llm_studio(self):
        """Open the LLM Studio window."""
        pass  # Placeholder for now
    
    def show_about(self):
        """Show the about dialog."""
        QMessageBox.about(self, "About AI Coder Assistant",
                         "AI Coder Assistant\n\n"
                         "A powerful AI-powered coding assistant.\n\n"
                         "Version: 1.0.0\n"
                         "© 2024 AI Coder Assistant Contributors")
    
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
        
        # 1. AI Model Configuration
        model_group = QGroupBox("1. AI Model Configuration")
        model_layout = QGridLayout()
        model_group.setLayout(model_layout)
        main_layout.addWidget(model_group)

        model_layout.addWidget(QLabel("Model Source:"), 0, 0)
        self.model_source_selector = QComboBox()
        self.model_source_selector.addItems(["Ollama", "Own Model", "OpenAI", "Google Gemini", "Claude"])
        model_layout.addWidget(self.model_source_selector, 0, 1)

        model_layout.addWidget(QLabel("Ollama Model:"), 1, 0)
        self.ollama_model_selector = QComboBox()
        model_layout.addWidget(self.ollama_model_selector, 1, 1)

        self.refresh_models_button = QPushButton("Refresh Models")
        model_layout.addWidget(self.refresh_models_button, 1, 2)

        model_layout.addWidget(QLabel("Own Model Status:"), 2, 0)
        self.own_model_status_label = QLabel("Not Loaded")
        model_layout.addWidget(self.own_model_status_label, 2, 1)

        self.load_model_button = QPushButton("Load Trained Model")
        model_layout.addWidget(self.load_model_button, 2, 2)

        # 2. Code Scanning
        scan_group = QGroupBox("2. Code Scanning")
        scan_layout = QGridLayout()
        scan_group.setLayout(scan_layout)
        main_layout.addWidget(scan_group)

        scan_layout.addWidget(QLabel("Include Patterns:"), 0, 0)
        self.include_patterns_edit = QLineEdit("*.py,*.js,*.java,*.cpp,*.c,*.h")
        scan_layout.addWidget(self.include_patterns_edit, 0, 1)

        scan_layout.addWidget(QLabel("Exclude Patterns:"), 1, 0)
        self.exclude_patterns_edit = QLineEdit("*/.venv/*,*/node_modules/*,*/tests/*,*.md")
        scan_layout.addWidget(self.exclude_patterns_edit, 1, 1)

        self.enable_ai_analysis_checkbox = QCheckBox("Enable AI-Powered Analysis")
        self.enable_ai_analysis_checkbox.setChecked(True)
        scan_layout.addWidget(self.enable_ai_analysis_checkbox, 2, 0)

        scan_layout.addWidget(QLabel("Project Directory:"), 3, 0)
        self.project_dir_edit = QLineEdit(os.getcwd())
        scan_layout.addWidget(self.project_dir_edit, 3, 1)

        self.browse_button = QPushButton("Browse...")
        scan_layout.addWidget(self.browse_button, 3, 2)

        self.start_scan_button = QPushButton("Start Scan")
        scan_layout.addWidget(self.start_scan_button, 4, 0, 1, 3)

        # 3. Results/Suggestions
        results_group = QGroupBox("3. Results/Suggestions")
        results_layout = QVBoxLayout()
        results_group.setLayout(results_layout)
        main_layout.addWidget(results_group)

        self.scan_results_text = QTextEdit()
        self.scan_results_text.setReadOnly(True)
        results_layout.addWidget(self.scan_results_text)
        
        # Create buttons layout
        buttons_layout = QHBoxLayout()
        results_layout.addLayout(buttons_layout)

        self.create_report_button = QPushButton("Create Report")
        self.create_report_button.setEnabled(False)
        buttons_layout.addWidget(self.create_report_button)

        self.enhance_button = QPushButton("Enhance with AI")
        self.enhance_button.setEnabled(False)
        buttons_layout.addWidget(self.enhance_button)

        self.review_suggestions_button = QPushButton("Review Suggestions")
        self.review_suggestions_button.setEnabled(False)
        buttons_layout.addWidget(self.review_suggestions_button)

        self.tab_widget.addTab(ai_tab, "AI Analysis")

    def _on_model_source_changed(self, new_source: str):
        """Handle changes in model source selection."""
        model_mode = new_source.lower().replace(" ", "_")
        
        if model_mode == "ollama":
            # For Ollama models, update the model reference when selection changes
            if hasattr(self, 'ollama_model_selector'):
                current_model = self.ollama_model_selector.currentText()
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
        
        # Add web scraping functionality to the data tab
        # The setup_data_tab function from data_tab_widgets.py should handle this
        # But we need to ensure the web scraping UI elements are available
        if not hasattr(self, 'doc_urls_input'):
            # Create web scraping UI elements if they don't exist
            self.doc_urls_input = QTextEdit()
            self.doc_urls_input.setPlaceholderText("Enter URLs here...")
            self.doc_urls_input.setMaximumHeight(DOC_URLS_INPUT_MAX_HEIGHT)
            
            self.scraping_mode_selector = QComboBox()
            self.scraping_mode_selector.addItems(["Simple (Single Page)", "Enhanced (Follow Links)"])
            
            self.max_pages_spinbox = QSpinBox()
            self.max_pages_spinbox.setRange(1, MAX_PAGES_SPINBOX_RANGE)
            self.max_pages_spinbox.setValue(DEFAULT_MAX_PAGES_SPINBOX_VALUE)
            
            self.max_depth_spinbox = QSpinBox()
            self.max_depth_spinbox.setRange(1, MAX_DEPTH_SPINBOX_RANGE)
            self.max_depth_spinbox.setValue(DEFAULT_MAX_DEPTH_SPINBOX_VALUE)
            
            self.same_domain_checkbox = QCheckBox("Same Domain Only")
            self.same_domain_checkbox.setChecked(True)
            
            self.start_scraping_button = QPushButton("Start Scraping")
            self.start_scraping_button.clicked.connect(self.start_doc_acquisition)
            
            self.stop_scraping_button = QPushButton("Stop")
            self.stop_scraping_button.clicked.connect(self.cancel_doc_acquisition)
            self.stop_scraping_button.setEnabled(False)
    
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
        code_standards_tab = CodeStandardsTab(self.backend_controller)
        self.tab_widget.addTab(code_standards_tab, "Code Standards")
    
    def setup_security_intelligence_tab(self):
        """Set up the security intelligence tab."""
        security_intelligence_tab = SecurityIntelligenceTab(self.backend_controller)
        self.tab_widget.addTab(security_intelligence_tab, "Security Intelligence")
    
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
            # AI Analysis Tab Signal Connections
            if hasattr(self, 'refresh_models_button'):
                self.refresh_models_button.clicked.connect(self.populate_ollama_models)
                logger.debug("Connected refresh_models_button")
            
            if hasattr(self, 'load_model_button'):
                self.load_model_button.clicked.connect(self.load_trained_model)
                logger.debug("Connected load_model_button")
            
            if hasattr(self, 'browse_button'):
                self.browse_button.clicked.connect(self.select_scan_directory)
                logger.debug("Connected browse_button")
            
            if hasattr(self, 'start_scan_button'):
                self.start_scan_button.clicked.connect(self.start_scan)
                logger.debug("Connected start_scan_button")
            
            if hasattr(self, 'create_report_button'):
                self.create_report_button.clicked.connect(self.start_report_generation)
                logger.debug("Connected create_report_button")
            
            if hasattr(self, 'enhance_button'):
                self.enhance_button.clicked.connect(self.start_ai_enhancement)
                logger.debug("Connected enhance_button")
            
            if hasattr(self, 'review_suggestions_button'):
                self.review_suggestions_button.clicked.connect(self.review_next_suggestion)
                logger.debug("Connected review_suggestions_button")
            
            # Model source selector connection
            if hasattr(self, 'model_source_selector'):
                self.model_source_selector.currentTextChanged.connect(self._on_model_source_changed)
                logger.debug("Connected model_source_selector")
            
            # Ollama model selector connection
            if hasattr(self, 'ollama_model_selector'):
                self.ollama_model_selector.currentTextChanged.connect(self._on_ollama_model_selected)
                logger.debug("Connected ollama_model_selector")
            
            # Data Tab Signal Connections (if they exist)
            if hasattr(self, 'start_scraping_button'):
                self.start_scraping_button.clicked.connect(self.start_doc_acquisition)
                logger.debug("Connected start_scraping_button")
            
            if hasattr(self, 'stop_scraping_button'):
                self.stop_scraping_button.clicked.connect(self.cancel_doc_acquisition)
                logger.debug("Connected stop_scraping_button")
            
            logger.debug("UI signals connected successfully.")
            
        except Exception as e:
            logger.error(f"Error connecting UI signals: {e}")
            # Don't raise the exception to prevent app startup failure
            # Just log the error and continue

    def populate_ollama_models(self):
        """Populate the Ollama model selector with available models."""
        try:
            models = get_available_models_sync()
            self.ollama_model_selector.clear()
            if models:
                self.ollama_model_selector.addItems(models)
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
                "Model Files (*.pth *.pt *.bin *.safetensors);;All Files (*)"
            )
            
            if not model_file:
                return
            
            self.log_message(f"Loading trained model from: {model_file}")
            
            # Update UI to show loading state
            self.own_model_status_label.setText("Loading...")
            self.load_model_button.setEnabled(False)
            
            # Start worker to load the model
            self.start_worker(
                'load_model',
                self._load_model_worker,
                model_file,
                callback=self._on_model_loaded,
                error_callback=self._on_model_load_error
            )
            
        except Exception as e:
            self.log_message(f"Error starting model load: {e}")
            self.own_model_status_label.setText("Load Failed")
            self.load_model_button.setEnabled(True)

    def _load_model_worker(self, model_file: str):
        """Worker function to load the trained model."""
        try:
            # This is a placeholder implementation
            # In a real implementation, you would load the model here
            # For now, we'll just simulate loading
            import time
            time.sleep(2)  # Simulate loading time
            
            return {
                'success': True,
                'model_file': model_file,
                'model_name': os.path.basename(model_file)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _on_model_loaded(self, result):
        """Handle successful model loading."""
        try:
            if result.get('success'):
                model_name = result.get('model_name', 'Unknown Model')
                self.current_model_ref = result.get('model_file')
                self.current_tokenizer_ref = None  # Set if you have a tokenizer
                self.own_model_status_label.setText(f"Loaded: {model_name}")
                self.log_message(f"Successfully loaded model: {model_name}")
            else:
                self.own_model_status_label.setText("Load Failed")
                self.log_message(f"Failed to load model: {result.get('error', 'Unknown error')}")
        except Exception as e:
            self.log_message(f"Error handling model load result: {e}")
        finally:
            self.load_model_button.setEnabled(True)

    def _on_model_load_error(self, error):
        """Handle model loading errors."""
        try:
            self.own_model_status_label.setText("Load Failed")
            self.load_model_button.setEnabled(True)
            self.log_message(f"Model loading error: {error}")
        except Exception as e:
            self.log_message(f"Error handling model load error: {e}")

    def select_scan_directory(self):
        """Select directory to scan for code analysis."""
        directory = QFileDialog.getExistingDirectory(self, "Select Directory to Scan")
        if directory:
            self.scan_directory = directory
            # Update the appropriate directory field based on which tab is active
            if hasattr(self, 'project_dir_edit'):
                self.project_dir_edit.setText(directory)
            if hasattr(self, 'scan_dir_entry'):
                self.scan_dir_entry.setText(directory)
            self.log_message(f"Selected scan directory: {directory}")

    def select_local_corpus_dir(self):
        dir_name = QFileDialog.getExistingDirectory(self, "Select Local Corpus Folder", settings.PROJECT_ROOT)
        if dir_name:
            self.local_files_label.setText(f"Selected: {os.path.basename(dir_name)}")
            settings.DOCS_DIR = dir_name

    def start_preprocessing(self):
        self.progress_dialog = QProgressDialog("Preprocessing...", "Cancel", PROGRESS_DIALOG_MIN_VALUE, PROGRESS_DIALOG_MAX_VALUE, self)
        self.progress_dialog.setWindowTitle("Preprocessing Progress")
        self.progress_dialog.setAutoClose(True)
        self.progress_dialog.setAutoReset(True)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.setValue(0)
        self.progress_dialog.show()
        reset_db = self.knowledge_mode_selector.currentText().startswith("Reset")
        self.start_worker('preprocess_docs', preprocess.build_vector_db, settings.DOCS_DIR, None, None, reset_db=reset_db, progress_callback=self.update_preprocess_progress)

    def review_next_suggestion(self):
        """Start reviewing the next suggestion in the list."""
        if not hasattr(self, 'suggestion_list') or not self.suggestion_list:
            QMessageBox.warning(self, "No Suggestions", "Please run a scan first to generate suggestions.")
            return
            
        if not hasattr(self, 'current_suggestion_index'):
            self.current_suggestion_index = 0
        
        if self.current_suggestion_index >= len(self.suggestion_list):
            QMessageBox.information(self, "Review Complete", "All suggestions have been reviewed.")
            self.current_suggestion_index = 0
            return
        
        suggestion = self.suggestion_list[self.current_suggestion_index]
        
        # Get model settings
        model_mode = self.model_source_selector.currentText().lower().replace(" ", "_")
        model_ref = self.current_model_ref
        tokenizer_ref = self.current_tokenizer_ref
        
        # Start worker to get AI explanation
        self.log_message(f"Getting AI explanation for suggestion {self.current_suggestion_index + 1}/{len(self.suggestion_list)}")
        self.start_worker(
            'get_explanation',
            ai_tools.get_ai_explanation,
            suggestion,
            model_mode,
            model_ref,
            tokenizer_ref,
            progress_callback=lambda c, t, m: None,  # No progress needed for single explanation
            log_message_callback=self.log_message
        )

    def apply_suggestion(self, suggestion):
        """Apply a code suggestion to the file."""
        try:
            file_path = suggestion.get('file_path')
            line_number = suggestion.get('line_number', 0)
            suggested_code = suggestion.get('suggested_improvement', '')
            
            if not file_path or not suggested_code or suggested_code == 'No suggestion available':
                self.log_message("No valid suggestion to apply")
                return
            
            # Read the file
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Apply the suggestion (replace the problematic line)
            if 0 <= line_number < len(lines):
                lines[line_number] = suggested_code + '\n'
                
                # Write back to file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                
                self.log_message(f"Applied suggestion to {file_path}:{line_number + 1}")
            else:
                self.log_message(f"Invalid line number {line_number} for file {file_path}")
                
        except Exception as e:
            self.log_message(f"Error applying suggestion: {e}")

    def start_youtube_transcription(self):
        youtube_url = self.youtube_url_entry.text()
        if not youtube_url: return
        self.start_worker('transcribe_youtube', ai_tools.transcribe_youtube_tool, youtube_url)

    @pyqtSlot(str)
    def log_message(self, message: str, level: str = "info") -> None:
        """Append a message to the log output widget."""
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
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
            if hasattr(self, 'log_output') and self.log_output:
                self.log_output.append(message)
                self.log_output.verticalScrollBar().setValue(
                    self.log_output.verticalScrollBar().maximum()
                )
        except Exception as e:
            print(f"Error in thread-safe log message: {e}")
            print(f"Original message: {message}")

    def start_report_generation(self):
        """Start generating a full markdown report with robust validation."""
        try:
            # Validate that we have suggestions to report
            if not hasattr(self, 'suggestion_list') or not self.suggestion_list:
                QMessageBox.warning(
                    self, 
                    "No Data for Report", 
                    "Please run a scan first to generate data for the report."
                )
                return

            # Validate model selection
            if not hasattr(self, 'model_source_selector'):
                QMessageBox.warning(
                    self, 
                    "Configuration Error", 
                    "Model source selector not found. Please restart the application."
                )
                return

            # Get model settings with validation
            model_mode = self.model_source_selector.currentText().lower().replace(" ", "_")
            model_ref = getattr(self, 'current_model_ref', None)
            tokenizer_ref = getattr(self, 'current_tokenizer_ref', None)

            # Validate model reference for AI-enhanced reports
            if model_mode == "ollama" and (not model_ref or model_ref is None):
                QMessageBox.warning(
                    self, 
                    "No Model Selected", 
                    "For AI-enhanced reports, please select an Ollama model first.\n\n"
                    "1. Go to the Model Management section\n"
                    "2. Select 'Ollama' as the model source\n"
                    "3. Choose a model from the dropdown\n"
                    "4. Try report generation again"
                )
                return

            # Create progress dialog
            self.report_progress_dialog = QProgressDialog("Generating report...", "Cancel", 0, 100, self)
            self.report_progress_dialog.setWindowTitle("Report Generation")
            self.report_progress_dialog.setAutoClose(True)
            self.report_progress_dialog.setAutoReset(True)
            self.report_progress_dialog.setMinimumDuration(0)
            self.report_progress_dialog.setValue(0)
            self.report_progress_dialog.show()

            # Start worker to generate report
            self.log_message("Starting report generation...")
            self.create_report_button.setEnabled(False)  # Disable button during generation
            
            self.start_worker(
                'generate_report',
                ai_tools.generate_report_and_training_data,
                self.suggestion_list,
                model_mode,
                model_ref,
                tokenizer_ref,
                progress_callback=self.update_report_progress,
                log_message_callback=self.log_message
            )
            
        except Exception as e:
            self.log_message(f"Error starting report generation: {e}")
            QMessageBox.critical(
                self, 
                "Report Generation Error", 
                f"Failed to start report generation:\n{str(e)}\n\nPlease check the logs for more details."
            )
            self.create_report_button.setEnabled(True)
            if hasattr(self, 'report_progress_dialog') and self.report_progress_dialog:
                self.report_progress_dialog.close()

    def update_report_progress(self, current: int, total: int, message: str):
        """Update report generation progress."""
        if hasattr(self, 'report_progress_dialog') and self.report_progress_dialog:
            self.report_progress_dialog.setRange(0, total)
            self.report_progress_dialog.setValue(current)
            self.report_progress_dialog.setLabelText(message)
            if current >= total:
                self.report_progress_dialog.setValue(total)

    def navigate_to_url(self):
        url_text = self.url_bar.text()
        if not url_text.startswith(('http://', 'https://')):
            url_text = 'https://' + url_text
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
        if hasattr(self, 'current_worker_id') and self.current_worker_id:
            self.log_message("Stopping scan operation...")
            self.executor.submit(lambda: None)  # Placeholder for cancellation
            self.current_worker_id = None
        
        # Reset UI state
        self.scan_button.setEnabled(True)
        self.stop_scan_button.setEnabled(False)
        
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

    def start_scan(self):
        self.scan_results_text.setPlainText("Starting code scan...")
        self.create_report_button.setEnabled(False)
        self.enhance_button.setEnabled(False)
        self.scan_directory = self.project_dir_edit.text()
        if not os.path.exists(self.scan_directory):
            QMessageBox.warning(self, "Invalid Directory", f"The directory '{self.scan_directory}' does not exist.")
            return

        self.progress_dialog = QProgressDialog("Scanning files...", "Cancel", PROGRESS_DIALOG_MIN_VALUE, PROGRESS_DIALOG_MAX_VALUE, self)
        self.progress_dialog.setWindowTitle("Scan Progress")
        self.progress_dialog.setAutoClose(True)
        self.progress_dialog.setAutoReset(True)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.setValue(0)
        self.progress_dialog.show()

        include_patterns = self.include_patterns_edit.text().split(',')
        exclude_patterns = self.exclude_patterns_edit.text().split(',')
        enable_ai_powered = self.enable_ai_analysis_checkbox.isChecked()

        self.start_worker(
            "local_scan",
            scanner.scan_code_local,
            directory=self.scan_directory,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
            enable_ai_powered=enable_ai_powered,
            progress_callback=self.update_scan_progress,
            model_name=self.current_model_ref,
            callback=self.handle_scan_complete
        )

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

    def handle_scan_complete(self, result):
        """
        Callback for when a scan is complete. Emits a signal to update the UI
        on the main thread. This method is called from the background thread.
        """
        self.scan_completed.emit(result or [])
        self.log_message("Scan complete.")
        self._handle_scan_complete_ui(result)

    @pyqtSlot(list)
    def _handle_scan_complete_ui(self, result):
        """Update the UI with scan results, running in the main thread."""
        try:
            self.scan_results = result  # Store results
            formatted_text = self.format_issues_for_display(result)
            self.scan_results_text.setText(formatted_text)
            self.log_message(f"Scan finished. Displaying {len(result)} files with issues.")
        except Exception as e:
            self.log_message(f"Error displaying scan results: {e}", "error")
        finally:
            self.start_scan_button.setEnabled(True)
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
        self.create_report_button.setEnabled(enabled)
        self.enhance_button.setEnabled(enabled)
        self.review_suggestions_button.setEnabled(enabled)

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
            QMessageBox.information(self, "Review Cancelled", "Code review process cancelled.")
        
        # Store user feedback if provided
        user_feedback = dialog.get_user_justification()
        if user_feedback:
            self.log_message(f"User feedback for suggestion {self.current_suggestion_index}: {user_feedback}")

    def refresh_ollama_models(self):
        """Refresh the list of available Ollama models."""
        try:
            from backend.services.ollama_client import get_available_models_sync
            
            # Get available models
            models = get_available_models_sync()
            
            if not models:
                self.log_message("No Ollama models found. Please ensure Ollama is running and models are installed.")
                return
            
            # Update model selector
            if hasattr(self, 'ollama_model_selector'):
                current_model = self.ollama_model_selector.currentText()
                self.ollama_model_selector.clear()
                self.ollama_model_selector.addItems(models)
                
                # Try to restore previous selection if it still exists
                if current_model in models:
                    self.ollama_model_selector.setCurrentText(current_model)
                elif models:
                    # Select first available model
                    self.ollama_model_selector.setCurrentText(models[0])
                    
                self.log_message(f"Found {len(models)} Ollama models")
        except Exception as e:
            self.log_message(f"Error refreshing Ollama models: {str(e)}")
            QMessageBox.warning(self, "Refresh Error", f"Failed to refresh Ollama models: {str(e)}")

    def start_ai_enhancement(self):
        """Starts AI enhancement of scan results in a background thread."""
        model_name = self.ollama_model_selector.currentText()
        if not model_name:
            QMessageBox.warning(self, "Model Not Selected", "Please select an Ollama model first.")
            return

        if not self.scan_results:
            QMessageBox.warning(self, "No Results", "Please run a scan first to generate results to enhance.")
            return

        self._enable_post_scan_buttons(False)
        
        self.progress_dialog = QProgressDialog("Enhancing with AI...", "Cancel", 0, len(self.scan_results), self)
        self.progress_dialog.setWindowTitle("AI Enhancement Progress")
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.show()

        future = self.executor.submit(
            scanner.enhance_issues_with_ai,
            self.scan_results,
            model_name,
            progress_callback=self.scan_progress_updated.emit
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
                    QTimer.singleShot(0, lambda: self._handle_scan_complete_ui(enhanced_results))
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
            file_path = file_result.get('file_path', 'N/A')
            issues = file_result.get('issues', [])
            if not issues:
                continue

            output_lines.append(f"--- {file_path} ({len(issues)} issues) ---")
            for issue in issues:
                line = issue.get('line', 'N/A')
                desc = issue.get('description', 'No description.')
                suggestion = issue.get('suggestion')

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
                self.progress_dialog.setLabelText(f"{message}\\nProgress: {current}/{total}")
                if current >= total:
                    self.progress_dialog.setValue(total)
        except Exception as e:
            self.log_message(f"Error updating preprocess progress: {e}")
            # Clean up the dialog if it's in an invalid state
            self.progress_dialog = None

    def start_base_training(self):
        """Start base model training with proper error handling."""
        try:
            self.progress_dialog = QProgressDialog("Training Base Model...", "Cancel", PROGRESS_DIALOG_MIN_VALUE, PROGRESS_DIALOG_MAX_VALUE, self)
            self.progress_dialog.setWindowTitle("Training Progress")
            self.progress_dialog.setAutoClose(True)
            self.progress_dialog.setAutoReset(True)
            self.progress_dialog.setMinimumDuration(0)
            self.progress_dialog.setValue(0)
            self.progress_dialog.show()
            self.start_worker('train_base', trainer.train_base_model, progress_callback=self.update_training_progress)
        except Exception as e:
            self.log_message(f"Error starting training: {e}")
            QMessageBox.critical(self, "Training Error", f"Failed to start training: {str(e)}")

    def update_training_progress(self, current: int, total: int, message: str):
        """Update training progress with proper error handling."""
        try:
            if self.progress_dialog is not None:
                self.progress_dialog.setRange(PROGRESS_DIALOG_MIN_VALUE, PROGRESS_DIALOG_MAX_VALUE)
                self.progress_dialog.setValue(current)
                self.progress_dialog.setLabelText(f"{message}\\nProgress: {current}/{total}")
                if current >= total:
                    self.progress_dialog.setValue(total)
        except Exception as e:
            self.log_message(f"Error updating training progress: {e}")
            # Clean up the dialog if it's in an invalid state
            self.progress_dialog = None

    def start_finetuning(self):
        """Start model finetuning with proper error handling."""
        try:
            self.progress_dialog = QProgressDialog("Finetuning Model...", "Cancel", PROGRESS_DIALOG_MIN_VALUE, PROGRESS_DIALOG_MAX_VALUE, self)
            self.progress_dialog.setWindowTitle("Finetuning Progress")
            self.progress_dialog.setAutoClose(True)
            self.progress_dialog.setAutoReset(True)
            self.progress_dialog.setMinimumDuration(0)
            self.progress_dialog.setValue(0)
            self.progress_dialog.show()
            self.start_worker('finetune', trainer.finetune_model, progress_callback=self.update_finetune_progress)
        except Exception as e:
            self.log_message(f"Error starting finetuning: {e}")
            QMessageBox.critical(self, "Finetuning Error", f"Failed to start finetuning: {str(e)}")

    def update_finetune_progress(self, current: int, total: int, message: str):
        """Update finetuning progress with proper error handling."""
        try:
            if self.progress_dialog is not None:
                self.progress_dialog.setRange(PROGRESS_DIALOG_MIN_VALUE, PROGRESS_DIALOG_MAX_VALUE)
                self.progress_dialog.setValue(current)
                self.progress_dialog.setLabelText(f"{message}\\nProgress: {current}/{total}")
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
                self.progress_dialog.setLabelText(f"{message}\\nProgress: {current}/{total}")
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
            file_path, _ = QFileDialog.getOpenFileName(self, "Select Dockerfile", "", "Dockerfile (*)")
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
            print(f"[DEBUG] context_dir={context_dir}, dockerfile_path={dockerfile_path}, build_args={build_args}, run_opts={run_opts}")
            # Call backend logic
            print("[DEBUG] About to call run_build_and_test_in_docker")
            result = run_build_and_test_in_docker(
                context_dir=context_dir,
                dockerfile_path=dockerfile_path,
                build_args=build_args,
                run_opts=run_opts,
                test_command="python run_tests.py"
            )
            print("[DEBUG] run_build_and_test_in_docker returned")
            # Show result to user
            if result.get("success"):
                QMessageBox.information(self, "Docker Build/Test Success", f"Stage: {result.get('stage')}\\nOutput:\\n{result.get('output')}")
            else:
                QMessageBox.critical(self, "Docker Build/Test Failed", f"Stage: {result.get('stage', 'unknown')}\\nError:\\n{result.get('output', result.get('error', 'Unknown error'))}")
        except Exception as e:
            self.log_message(f"Error testing Docker: {e}")
            QMessageBox.critical(self, "Docker Test Error", f"Failed to test Docker: {str(e)}")

    def start_worker(self, worker_id: str, target_func, *args, **kwargs):
        """Start a background task using ThreadPoolExecutor."""
        try:
            original_callback = kwargs.pop('callback', None)
            def cleanup_callback(future):
                result = None
                try:
                    result = future.result()
                except Exception as e:
                    # Log error in the main thread, capturing the exception's value
                    QTimer.singleShot(0, lambda err=e: self.log_message(f"Error in worker {worker_id}: {err}"))

                if original_callback:
                    # Ensure original callback also runs in the main thread
                    QTimer.singleShot(0, lambda: original_callback(result))

                # Update active workers list in the main thread
                QTimer.singleShot(0, lambda: self.active_workers.remove(worker_id) if worker_id in self.active_workers else None)
                
            future = self.executor.submit(target_func, *args, **kwargs)
            self.active_workers.append(worker_id)
            future.add_done_callback(cleanup_callback)
        except Exception as e:
            self.log_message(f"Error starting worker {worker_id}: {e}")
            if self.progress_dialog is not None:
                try:
                    self.progress_dialog.close()
                except Exception as close_error:
                    self.log_message(f"Error closing progress dialog: {close_error}", "error")
                finally:
                    self.progress_dialog = None
            raise