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
import sys
import os
import torch
import logging
import time
from PyQt6.QtWidgets import (QMainWindow, QTabWidget, QApplication, QWidget,
                             QPushButton, QMessageBox, QFileDialog, QProgressDialog,
                             QTextEdit, QVBoxLayout, QLabel, QHBoxLayout)
from PyQt6.QtCore import QUrl, pyqtSlot, Qt
from PyQt6.QtGui import QIcon

from .browser_tab import setup_browser_tab
from .data_tab_widgets import setup_data_tab
from .ai_tab_widgets import setup_ai_tab
from .ollama_export_tab import setup_ollama_export_tab
from .continuous_learning_tab import ContinuousLearningTab
from .refactoring_tab import RefactoringTab
from .cloud_models_tab import CloudModelsTab
from .worker_threads import Worker
from .suggestion_dialog import SuggestionDialog
from .markdown_viewer import MarkdownViewerDialog
from ...backend.services.studio_ui import LLMStudioUI

from ...backend.services import ai_tools, scanner, ollama_client
from ...backend.services import acquire, preprocess
from ...backend.services import trainer
from ...backend.utils import settings
from ...utils.constants import (
    WINDOW_DEFAULT_X, WINDOW_DEFAULT_Y, WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT,
    LOG_CONSOLE_MAX_HEIGHT, PROGRESS_MIN, PROGRESS_MAX, GRACEFUL_SHUTDOWN_WAIT,
    PERCENTAGE_MULTIPLIER, GRACEFUL_SHUTDOWN_WAIT_MS, WAIT_TIMEOUT_MS, DEFAULT_PERCENTAGE_MULTIPLIER,
    PROGRESS_DIALOG_MAX_VALUE, PROGRESS_DIALOG_MIN_VALUE, MAX_FILE_SIZE_KB
)

from transformers import GPT2Tokenizer, GPT2LMHeadModel


# Set up a logger for this module
logger = logging.getLogger(__name__)

class AICoderAssistant(QMainWindow):
    def __init__(self):
        super().__init__()
        logger.info("Initializing Main Window...")
        self.setWindowTitle("AI Coder Assistant")
        self.setGeometry(WINDOW_DEFAULT_X, WINDOW_DEFAULT_Y, WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT)
        
        self.worker = None
        self.progress_dialog = None
        self.suggestion_list = []
        self.current_suggestion_index = 0
        self.own_trained_model = None
        self.own_tokenizer = None
        self.scan_cancelled = False  # Flag for scan cancellation
        self.scan_directory = None  # Directory to scan
        self.current_model_ref = None  # Current model reference
        self.current_tokenizer_ref = None  # Current tokenizer reference
        
        main_container = QWidget()
        self.main_layout = QVBoxLayout(main_container)
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)
        self.setCentralWidget(main_container)
        
        # Create menu bar
        self.create_menu_bar()
        
        self.ai_tab = QWidget()
        self.data_tab = QWidget()
        self.browser_tab = QWidget()
        self.ollama_export_tab = QWidget()
        
        setup_ai_tab(self.ai_tab, self)
        setup_data_tab(self.data_tab, self)
        setup_browser_tab(self.browser_tab, self)
        setup_ollama_export_tab(self.ollama_export_tab, self)
        
        # Create LLM Studio tab
        self.llm_studio_tab = LLMStudioUI()
        
        # Add AI PR Creation tab (enterprise feature)
        from .pr_tab_widgets import PRCreationTab
        self.pr_tab = PRCreationTab()
        self.tabs.addTab(self.pr_tab, "AI PR Creation")
        
        self.tabs.addTab(self.ai_tab, "AI Agent")
        self.tabs.addTab(self.data_tab, "Data & Training")
        self.tabs.addTab(self.browser_tab, "Browser & Transcription")
        self.tabs.addTab(self.ollama_export_tab, "Export to Ollama")
        self.tabs.addTab(self.llm_studio_tab, "LLM Studio")
        
        # Add Continuous Learning tab
        self.continuous_learning_tab = ContinuousLearningTab()
        self.tabs.addTab(self.continuous_learning_tab, "Continuous Learning")
        
        # Add Advanced Refactoring tab
        self.refactoring_tab = RefactoringTab()
        self.tabs.addTab(self.refactoring_tab, "Advanced Refactoring")
        
        # Add Cloud Models tab
        self.cloud_models_tab = CloudModelsTab()
        self.tabs.addTab(self.cloud_models_tab, "Cloud Models")
        
        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setMaximumHeight(LOG_CONSOLE_MAX_HEIGHT)
        self.main_layout.addWidget(self.log_console)

        self._connect_signals()
        self.populate_ollama_models()
        self.on_model_source_changed()
        logger.info("Main Window Initialized Successfully.")

        # Add a list to keep references to all running workers
        self.active_workers = []

    def create_menu_bar(self):
        """Create the application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('&File')
        
        # LLM Studio menu
        llm_menu = menubar.addMenu('&LLM Studio')
        
        # Add LLM Studio actions
        open_llm_studio_action = llm_menu.addAction('Open LLM Studio')
        open_llm_studio_action.triggered.connect(self.open_llm_studio)
        
        # Help menu
        help_menu = menubar.addMenu('&Help')
        
        about_action = help_menu.addAction('About')
        about_action.triggered.connect(self.show_about)

    def open_llm_studio(self):
        """Open LLM Studio in a new window."""
        try:
            from ...backend.services.studio_ui import LLMStudioUI
            self.llm_studio_window = LLMStudioUI()
            self.llm_studio_window.show()
            self.log_message("LLM Studio opened in new window")
        except Exception as e:
            self.log_message(f"Error opening LLM Studio: {e}")
            QMessageBox.critical(self, "Error", f"Could not open LLM Studio: {e}")

    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(self, "About AI Coder Assistant", 
                         "AI Coder Assistant\n\n"
                         "A comprehensive AI-powered code analysis and development tool.\n\n"
                         "Features:\n"
                         "• AI-powered code scanning and analysis\n"
                         "• Multi-provider LLM support (OpenAI, Google Gemini, Claude)\n"
                         "• PR creation with AI-generated fixes\n"
                         "• Code quality improvements\n"
                         "• Training and fine-tuning capabilities\n"
                         "• Browser integration and transcription\n\n"
                         "Version: 2.0.0")

    def _connect_signals(self):
        logger.debug("Connecting UI signals...")
        # AI Tab signals
        self.refresh_button.clicked.connect(self.populate_ollama_models)
        self.browse_button.clicked.connect(self.select_scan_directory)
        self.model_source_selector.currentIndexChanged.connect(self.on_model_source_changed)
        self.load_model_button.clicked.connect(self.load_own_trained_model)
        self.scan_button.clicked.connect(self.start_scan)
        self.stop_scan_button.clicked.connect(self.stop_scan)
        self.review_suggestions_button.clicked.connect(self.review_next_suggestion)
        self.create_report_button.clicked.connect(self.start_report_generation)
        
        # Data Tab signals
        self.add_local_files_button.clicked.connect(self.select_local_corpus_dir)
        self.acquire_doc_button.clicked.connect(self.start_doc_acquisition)
        self.preprocess_docs_button.clicked.connect(self.start_preprocessing)
        self.train_lm_button.clicked.connect(self.start_base_training)
        self.finetune_lm_button.clicked.connect(self.start_finetuning)
        
        # Browser Tab signals
        self.go_button.clicked.connect(self.navigate_to_url)
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        self.browser.urlChanged.connect(self.update_url_bar)
        self.transcribe_button.clicked.connect(self.start_youtube_transcription)
        logger.debug("UI signals connected.")

    def on_model_source_changed(self):
        is_ollama = self.model_source_selector.currentText() == "Ollama"
        self.ollama_model_selector.setVisible(is_ollama)
        self.refresh_button.setVisible(is_ollama)
        self.load_model_button.setVisible(not is_ollama)
        self.model_status_label.setVisible(not is_ollama)
        
        # Set current model references
        if is_ollama:
            self.current_model_ref = self.ollama_model_selector.currentText()
            self.current_tokenizer_ref = None
        else:
            self.current_model_ref = self.own_trained_model
            self.current_tokenizer_ref = self.own_tokenizer
            if not is_ollama: 
                self.load_own_trained_model()

    def load_own_trained_model(self):
        model_path = settings.MODEL_SAVE_PATH
        if not os.path.exists(os.path.join(model_path, "config.json")):
            self.log_message("Own model not found. Please train a model first.")
            self.model_status_label.setText("Status: Model Not Found")
            return
        
        try:
            self.log_message(f"Loading tokenizer and model from {model_path}")
            device = torch.device(settings.DEVICE)
            self.own_tokenizer = GPT2Tokenizer.from_pretrained(model_path)
            self.own_trained_model = GPT2LMHeadModel.from_pretrained(model_path).to(device)
            self.own_trained_model.eval()
            self.log_message("Own trained model loaded successfully.")
            self.model_status_label.setText("Status: Model Loaded")
        except Exception as e:
            self.log_message(f"Failed to load own model: {e}")
            self.model_status_label.setText("Status: Error Loading Model")
            QMessageBox.critical(self, "Model Load Error", f"Could not load the model.\nError: {e}")

    def start_worker(self, task_type, func, *args, **kwargs):
        """Start a background worker thread for the given task."""
        worker = Worker(func, *args, **kwargs)
        self.current_worker = worker
        self.active_workers.append(worker)
        worker.finished.connect(lambda result: self.handle_worker_finished(task_type, result))
        worker.error.connect(lambda error: self.handle_worker_error(task_type, error))
        
        # Connect progress signal to appropriate update method
        if task_type == 'scan_code':
            worker.progress.connect(self.update_scan_progress)
        elif task_type == 'generate_report':
            worker.progress.connect(self.update_report_progress)
        elif task_type == 'preprocess_docs':
            worker.progress.connect(self.update_preprocess_progress)
        elif task_type == 'train_lm_base':
            worker.progress.connect(self.update_training_progress)
        elif task_type == 'train_lm_finetune':
            worker.progress.connect(self.update_finetune_progress)
        else:
            # Default progress handler
            worker.progress.connect(self.update_generic_progress)
        
        # Connect cancellation
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.canceled.connect(worker.cancel)
        if hasattr(self, 'report_progress_dialog') and self.report_progress_dialog:
            self.report_progress_dialog.canceled.connect(worker.cancel)
        
        worker.start()
        self.log_message(f"Started {task_type} worker thread")
    
    def handle_worker_finished(self, task_type, result):
        """Handle worker thread completion."""
        if self.current_worker in self.active_workers:
            self.active_workers.remove(self.current_worker)
        self.current_worker = None
        
        if task_type == 'scan_code':
            self.handle_scan_complete(result)
        elif task_type == 'generate_report':
            self.handle_report_complete(result)
        elif task_type == 'get_explanation':
            self.handle_explanation_complete(result)
        elif task_type == 'acquire_docs':
            if hasattr(self, 'progress_dialog') and self.progress_dialog:
                self.progress_dialog.close()
            if isinstance(result, dict) and 'success_count' in result:
                summary = (f"Document acquisition complete.\n"
                           f"Successfully scraped: {result['success_count']} / {result['total']} URLs.\n"
                           f"Files: {len(result.get('files', []))}\n"
                           f"URLs: {', '.join(result.get('urls', [])[:5])}{'...' if len(result.get('urls', [])) > 5 else ''}")
                if result.get('errors'):
                    summary += f"\nErrors: {len(result['errors'])}"
                self.log_message(summary)
                QMessageBox.information(self, "Acquisition Summary", summary)
            elif isinstance(result, str) and (result.startswith('No documents were acquired') or result.startswith('Error')):
                self.log_message(result)
                QMessageBox.warning(self, "Acquisition Failed", result)
            else:
                self.log_message("Document acquisition complete.")
        elif task_type == 'preprocess_docs':
            if hasattr(self, 'progress_dialog') and self.progress_dialog:
                self.progress_dialog.close()
            if isinstance(result, str) and (result.startswith('No files found') or result.startswith('Error')):
                self.log_message(result)
                QMessageBox.warning(self, "Preprocessing Failed", result)
            else:
                self.log_message("Preprocessing complete.")
        elif task_type == 'train_lm_base':
            if hasattr(self, 'progress_dialog') and self.progress_dialog:
                self.progress_dialog.close()
            if isinstance(result, str) and result.startswith('Error'):
                self.log_message(result)
                QMessageBox.warning(self, "Training Failed", result)
            else:
                self.log_message("Base model training complete.")
        else:
            self.log_message(f"Worker {task_type} completed")
    
    def handle_worker_error(self, task_type, error):
        """Handle worker thread errors."""
        if self.current_worker in self.active_workers:
            self.active_workers.remove(self.current_worker)
        self.current_worker = None
        
        # Reset UI state based on task type
        if task_type == 'scan_code':
            self.scan_button.setEnabled(True)
            self.stop_scan_button.setEnabled(False)
            if hasattr(self, 'progress_dialog') and self.progress_dialog:
                self.progress_dialog.close()
        elif task_type == 'generate_report':
            self.create_report_button.setEnabled(True)
            if hasattr(self, 'report_progress_dialog') and self.report_progress_dialog:
                self.report_progress_dialog.close()
        
        self.log_message(f"Error in {task_type}: {error}")
        QMessageBox.critical(self, f"{task_type.title()} Error", f"An error occurred: {error}")
    
    def handle_scan_complete(self, result):
        """Handle scan completion."""
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.close()
        
        self.scan_button.setEnabled(True)
        self.stop_scan_button.setEnabled(False)
        
        if result:
            self.suggestion_list = result
            total_issues = len(self.suggestion_list)
            
            # Generate summary
            summary_text = f"Scan completed successfully!\n\n"
            summary_text += f"Total issues found: {total_issues}\n\n"
            
            if total_issues > 0:
                # Group issues by type
                issues_by_type = {}
                for suggestion in self.suggestion_list:
                    issue_type = suggestion.get('issue_type', 'unknown')
                    issues_by_type[issue_type] = issues_by_type.get(issue_type, 0) + 1
                
                summary_text += "Issues by type:\n"
                for issue_type, count in sorted(issues_by_type.items()):
                    summary_text += f"  - {issue_type.replace('_', ' ').title()}: {count}\n"
                
                self.review_suggestions_button.setEnabled(True)
                self.create_report_button.setEnabled(True)
                
                # Add debug logging for interactive mode
                self.log_message(f"Interactive mode ready: {len(self.suggestion_list)} suggestions available for review")
            else:
                self.log_message("No suggestions found - interactive mode not available")
            
            self.scan_results_text.setText(summary_text)
        else:
            self.scan_results_text.setText("Scan completed but no issues were found.")
            self.log_message("Scan completed - no issues found")
    
    def handle_report_complete(self, result):
        """Handle report generation completion."""
        if hasattr(self, 'report_progress_dialog') and self.report_progress_dialog:
            self.report_progress_dialog.close()
        
        self.create_report_button.setEnabled(True)
        
        if result:
            markdown_report, jsonl_training_data = result
            
            # Show the report in the markdown viewer
            self.markdown_viewer = MarkdownViewerDialog(markdown_report, self)
            self.markdown_viewer.show()
            
            # Also save to file as backup
            try:
                report_path = os.path.join(settings.PROJECT_ROOT, "reports", f"ai_code_review_report_{int(time.time())}.md")
                os.makedirs(os.path.dirname(report_path), exist_ok=True)
                
                with open(report_path, 'w', encoding='utf-8') as f:
                    f.write(markdown_report)
                
                self.log_message(f"Report saved to: {report_path}")
            except Exception as e:
                self.log_message(f"Error saving report backup: {e}")
            
            # Save training data
            if jsonl_training_data:
                try:
                    training_path = os.path.join(settings.PROJECT_ROOT, "data", "training", f"training_data_{int(time.time())}.jsonl")
                    os.makedirs(os.path.dirname(training_path), exist_ok=True)
                    
                    with open(training_path, 'w', encoding='utf-8') as f:
                        f.write(jsonl_training_data)
                    
                    self.log_message(f"Training data saved to: {training_path}")
                except Exception as e:
                    self.log_message(f"Error saving training data: {e}")
            
            self.log_message("Report generation complete!")
        else:
            self.log_message("Error: No report generated")
    
    def handle_explanation_complete(self, result):
        """Handle AI explanation completion."""
        self.review_suggestions_button.setEnabled(True)
        if self.current_suggestion_index < len(self.suggestion_list):
            suggestion = self.suggestion_list[self.current_suggestion_index]
            
            # Ensure we have a valid explanation, even if it's an error message
            if not result or (isinstance(result, str) and result.startswith("Could not generate explanation:")):
                # Use a fallback explanation if the AI failed
                result = f"This suggestion addresses the identified issue: {suggestion.get('description', 'Unknown issue')}\n\nNote: AI explanation generation failed, but the suggestion is still valid based on static analysis."
            
            # Show the suggestion dialog
            dialog = SuggestionDialog(suggestion, result, self)
            result_code = dialog.exec()
            
            if result_code == SuggestionDialog.ApplyCode:
                # Apply the suggestion
                self.apply_suggestion(suggestion)
                self.current_suggestion_index += 1
                if self.current_suggestion_index < len(self.suggestion_list):
                    self.review_next_suggestion()
                else:
                    self.log_message("All suggestions reviewed!")
            elif result_code == SuggestionDialog.CancelAllCode:
                self.log_message("Review cancelled by user")
            else:
                # Skip this suggestion
                self.current_suggestion_index += 1
                if self.current_suggestion_index < len(self.suggestion_list):
                    self.review_next_suggestion()
                else:
                    self.log_message("All suggestions reviewed!")
    
    def populate_ollama_models(self):
        """Populate the Ollama model selector with available models."""
        try:
            models = ollama_client.get_available_models()
            self.ollama_model_selector.clear()
            if models:
                self.ollama_model_selector.addItems(models)
                self.log_message(f"Found {len(models)} Ollama models")
            else:
                self.log_message("No Ollama models found")
        except Exception as e:
            self.log_message(f"Error getting Ollama models: {e}")

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

    def select_scan_directory(self):
        """Select directory to scan for code analysis."""
        directory = QFileDialog.getExistingDirectory(self, "Select Directory to Scan")
        if directory:
            self.scan_directory = directory
            self.scan_dir_entry.setText(directory)
            self.log_message(f"Selected scan directory: {directory}")

    def review_next_suggestion(self):
        """Start reviewing the next suggestion in the list."""
        if not self.suggestion_list or self.current_suggestion_index >= len(self.suggestion_list):
            self.log_message("No more suggestions to review")
            return
        
        suggestion = self.suggestion_list[self.current_suggestion_index]
        
        # Get model settings
        model_mode = self.model_source_selector.currentText().lower().replace(" ", "_")
        model_ref = self.current_model_ref
        tokenizer_ref = self.current_tokenizer_ref
        
        # Get AI explanation for the suggestion
        self.start_worker('get_explanation', ai_tools.get_ai_explanation, 
                         suggestion, model_mode, model_ref, tokenizer_ref)

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
        
        self.log_message(f"Starting {scraping_mode.lower()} acquisition from {len(urls)} URLs...")
        self.log_message(f"Parameters: max_pages={max_pages}, max_depth={max_depth}, same_domain_only={same_domain_only}")
        
        self.progress_dialog = QProgressDialog("Acquiring Docs...", "Cancel", PROGRESS_MIN, PROGRESS_MAX, self)
        self.progress_dialog.show()
        
        # Choose the appropriate crawling function based on mode
        if "Enhanced" in scraping_mode:
            links_per_page = self.links_per_page_spinbox.value()
            self.start_worker('acquire_docs', acquire.crawl_docs, urls, settings.DOCS_DIR,
                            max_pages=max_pages, max_depth=max_depth, same_domain_only=same_domain_only, links_per_page=links_per_page)
        else:
            self.start_worker('acquire_docs', acquire.crawl_docs_simple, urls, settings.DOCS_DIR)

    def start_youtube_transcription(self):
        youtube_url = self.youtube_url_entry.text()
        if not youtube_url: return
        self.start_worker('transcribe_youtube', ai_tools.transcribe_youtube_tool, youtube_url)

    @pyqtSlot(str)
    def log_message(self, message):
        self.log_console.append(message)
    
    def start_report_generation(self):
        if not self.suggestion_list:
            QMessageBox.warning(self, "No Suggestions", "Please run a scan first to generate suggestions.")
            return
        self.log_message("=== REPORT GENERATION START ===")
        self.log_message(f"Starting report generation for {len(self.suggestion_list)} suggestions")
        self.report_progress_dialog = QProgressDialog("Generating report...", "Cancel", 0, len(self.suggestion_list), self)
        self.report_progress_dialog.setWindowTitle("Report Generation Progress")
        self.report_progress_dialog.setAutoClose(True)
        self.report_progress_dialog.setAutoReset(True)
        self.report_progress_dialog.setMinimumDuration(0)
        self.report_progress_dialog.setValue(0)
        self.report_progress_dialog.show()
        self.log_message("Report progress dialog initialized")
        model_mode = self.model_source_selector.currentText().lower().replace(" ", "_")
        model_ref = self.current_model_ref
        tokenizer_ref = self.current_tokenizer_ref
        self.log_message(f"Report model settings - Mode: {model_mode}, Ref: {type(model_ref).__name__}")
        self.log_message("Starting report generation worker...")
        self.start_worker('generate_report', ai_tools.generate_report_and_training_data, 
                         self.suggestion_list, model_mode, model_ref, tokenizer_ref,
                         progress_callback=self.update_report_progress)
        self.log_message("=== REPORT GENERATION INITIALIZED ===")

    def update_report_progress(self, current: int, total: int, message: str):
        if hasattr(self, 'report_progress_dialog') and self.report_progress_dialog:
            self.report_progress_dialog.setRange(0, total)
            self.report_progress_dialog.setValue(current)
            self.report_progress_dialog.setLabelText(f"{message}\nProgress: {current}/{total}")
            QApplication.processEvents()
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
        logger.info("Application shutting down, cleaning up...")
        
        # Stop any running worker threads
        for worker in self.active_workers:
            if worker.isRunning():
                worker.quit()
                worker.wait(WAIT_TIMEOUT_MS)
        self.active_workers.clear()
        
        # Close progress dialog if open
        try:
            if hasattr(self, 'progress_dialog') and self.progress_dialog and self.progress_dialog.isVisible():
                self.progress_dialog.close()
                self.progress_dialog = None
        except Exception as e:
            logger.warning(f"Error closing progress dialog: {e}")
        
        # Close report progress dialog if open
        try:
            if hasattr(self, 'report_progress_dialog') and self.report_progress_dialog and self.report_progress_dialog.isVisible():
                self.report_progress_dialog.close()
                self.report_progress_dialog = None
        except Exception as e:
            logger.warning(f"Error closing report progress dialog: {e}")
        
        # Clean up PyTorch models to free GPU memory
        if hasattr(self, 'own_trained_model') and self.own_trained_model is not None:
            try:
                del self.own_trained_model
                del self.own_tokenizer
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                logger.info("PyTorch models cleaned up")
            except Exception as e:
                logger.warning(f"Error cleaning up PyTorch models: {e}")
        
        # Force garbage collection
        try:
            import gc
            gc.collect()
        except Exception as e:
            logger.warning(f"Error during garbage collection: {e}")
        
        logger.info("Cleanup complete")
        event.accept()

    def stop_scan(self):
        """Stop the current scan operation."""
        if hasattr(self, 'current_worker') and self.current_worker:
            self.log_message("Stopping scan operation...")
            self.current_worker.cancel()  # Use the improved cancel method
            self.current_worker = None
        
        # Reset UI state
        self.scan_button.setEnabled(True)
        self.stop_scan_button.setEnabled(False)
        
        # Close progress dialog if open
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.close()
        
        # Force garbage collection
        import gc
        gc.collect()
        
        self.log_message("Scan operation stopped by user")

    def start_scan(self):
        """Start the code scanning process."""
        if not self.scan_directory:
            QMessageBox.warning(self, "No Directory Selected", "Please select a directory to scan first.")
            return
        
        self.log_message("=== SCAN START ===")
        self.log_message(f"Starting scan of directory: {self.scan_directory}")
        
        # Get scan configuration
        scan_config = {
            'include_patterns': self.include_patterns_input.text().split(',') if self.include_patterns_input.text() else ['*.py', '*.js', '*.java', '*.cpp', '*.c', '*.h'],
            'exclude_patterns': self.exclude_patterns_input.text().split(',') if self.exclude_patterns_input.text() else [],
            'max_file_size_kb': MAX_FILE_SIZE_KB,
            'use_ai_enhancement': self.ai_enhancement_checkbox.isChecked(),
            'model_mode': self.model_source_selector.currentText().lower().replace(" ", "_"),
            'model_ref': self.current_model_ref,
            'tokenizer_ref': self.current_tokenizer_ref
        }
        
        self.log_message(f"Scan configuration: {scan_config}")
        
        self.progress_dialog = QProgressDialog("Initializing scan...", "Cancel", PROGRESS_DIALOG_MIN_VALUE, PROGRESS_DIALOG_MAX_VALUE, self)
        self.progress_dialog.setWindowTitle("Scan Progress")
        self.progress_dialog.setAutoClose(True)
        self.progress_dialog.setAutoReset(True)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.setValue(0)
        self.progress_dialog.show()
        
        self.start_worker(
            'scan_code',
            scanner.scan_code,
            self.scan_directory,
            scan_config,
            self.current_model_ref,
            self.current_tokenizer_ref,
            progress_callback=self.update_scan_progress
        )
        self.log_message("=== SCAN INITIALIZED ===")

    def update_scan_progress(self, current: int, total: int, message: str):
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.setRange(PROGRESS_DIALOG_MIN_VALUE, PROGRESS_DIALOG_MAX_VALUE)
            self.progress_dialog.setValue(current)
            self.progress_dialog.setLabelText(f"{message}\nProgress: {current}/{total}")
            QApplication.processEvents()
            if current >= total:
                self.progress_dialog.setValue(total)

    def update_preprocess_progress(self, current: int, total: int, message: str):
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.setRange(0, total)
            self.progress_dialog.setValue(current)
            self.progress_dialog.setLabelText(f"{message}\nProgress: {current}/{total}")
            QApplication.processEvents()
            if current >= total:
                self.progress_dialog.setValue(total)

    def start_base_training(self):
        self.progress_dialog = QProgressDialog("Training Base Model...", "Cancel", PROGRESS_DIALOG_MIN_VALUE, PROGRESS_DIALOG_MAX_VALUE, self)
        self.progress_dialog.setWindowTitle("Training Progress")
        self.progress_dialog.setAutoClose(True)
        self.progress_dialog.setAutoReset(True)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.setValue(0)
        self.progress_dialog.show()
        self.start_worker('train_base', trainer.train_base_model, progress_callback=self.update_training_progress)

    def update_training_progress(self, current: int, total: int, message: str):
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.setRange(PROGRESS_DIALOG_MIN_VALUE, PROGRESS_DIALOG_MAX_VALUE)
            self.progress_dialog.setValue(current)
            self.progress_dialog.setLabelText(f"{message}\nProgress: {current}/{total}")
            QApplication.processEvents()
            if current >= total:
                self.progress_dialog.setValue(total)

    def start_finetuning(self):
        self.progress_dialog = QProgressDialog("Finetuning Model...", "Cancel", PROGRESS_DIALOG_MIN_VALUE, PROGRESS_DIALOG_MAX_VALUE, self)
        self.progress_dialog.setWindowTitle("Finetuning Progress")
        self.progress_dialog.setAutoClose(True)
        self.progress_dialog.setAutoReset(True)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.setValue(0)
        self.progress_dialog.show()
        self.start_worker('finetune', trainer.finetune_model, progress_callback=self.update_finetune_progress)

    def update_finetune_progress(self, current: int, total: int, message: str):
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.setRange(PROGRESS_DIALOG_MIN_VALUE, PROGRESS_DIALOG_MAX_VALUE)
            self.progress_dialog.setValue(current)
            self.progress_dialog.setLabelText(f"{message}\nProgress: {current}/{total}")
            QApplication.processEvents()
            if current >= total:
                self.progress_dialog.setValue(total)

    def update_generic_progress(self, current: int, total: int, message: str):
        """Generic progress update handler for tasks without specific progress dialogs."""
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.setRange(0, total)
            self.progress_dialog.setValue(current)
            self.progress_dialog.setLabelText(f"{message}\nProgress: {current}/{total}")
            QApplication.processEvents()
            if current >= total:
                self.progress_dialog.setValue(total)