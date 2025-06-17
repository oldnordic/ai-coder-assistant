# src/ui/main_window.py
import sys
import os
import torch
import logging
from PyQt6.QtWidgets import (QMainWindow, QTabWidget, QApplication, QWidget,
                             QPushButton, QMessageBox, QFileDialog, QProgressDialog,
                             QTextEdit, QVBoxLayout)
from PyQt6.QtCore import QUrl, pyqtSlot, Qt
from PyQt6.QtGui import QIcon

from .browser_tab import setup_browser_tab
from .data_tab_widgets import setup_data_tab
from .ai_tab_widgets import setup_ai_tab
from .ollama_export_tab import setup_ollama_export_tab
from .worker_threads import Worker
from .suggestion_dialog import SuggestionDialog

from ..core import ai_tools, scanner, ollama_client
from ..training import trainer
from ..processing import acquire, preprocess
from ..config import settings # <-- FIXED

from transformers import GPT2Tokenizer, GPT2LMHeadModel


# Set up a logger for this module
logger = logging.getLogger(__name__)

class AICoderAssistant(QMainWindow):
    def __init__(self):
        super().__init__()
        logger.info("Initializing Main Window...")
        self.setWindowTitle("AI Coder Assistant")
        self.setGeometry(100, 100, 1200, 800)
        
        self.worker = None
        self.progress_dialog = None
        self.suggestion_list = []
        self.current_suggestion_index = 0
        self.own_trained_model = None
        self.own_tokenizer = None
        
        main_container = QWidget()
        self.main_layout = QVBoxLayout(main_container)
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)
        self.setCentralWidget(main_container)
        
        self.ai_tab = QWidget()
        self.data_tab = QWidget()
        self.browser_tab = QWidget()
        self.ollama_export_tab = QWidget()
        
        setup_ai_tab(self.ai_tab, self)
        setup_data_tab(self.data_tab, self)
        setup_browser_tab(self.browser_tab, self)
        setup_ollama_export_tab(self.ollama_export_tab, self)
        
        self.tabs.addTab(self.ai_tab, "AI Agent")
        self.tabs.addTab(self.data_tab, "Data & Training")
        self.tabs.addTab(self.browser_tab, "Browser & Transcription")
        self.tabs.addTab(self.ollama_export_tab, "Export to Ollama")
        
        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setMaximumHeight(150)
        self.main_layout.addWidget(self.log_console)

        self._connect_signals()
        self.populate_ollama_models()
        self.on_model_source_changed()
        logger.info("Main Window Initialized Successfully.")

    def _connect_signals(self):
        logger.debug("Connecting UI signals...")
        # AI Tab signals
        self.refresh_button.clicked.connect(self.populate_ollama_models)
        self.browse_button.clicked.connect(self.select_scan_directory)
        self.model_source_selector.currentIndexChanged.connect(self.on_model_source_changed)
        self.load_model_button.clicked.connect(self.load_own_trained_model)
        self.scan_button.clicked.connect(self.start_code_scan)
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
        if not is_ollama: self.load_own_trained_model()

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
        self.worker = Worker(task_type, func, *args, **kwargs)
        self.worker.signals.finished.connect(self.on_worker_finished)
        self.worker.signals.error.connect(self.on_worker_error)
        self.worker.signals.progress.connect(self.update_progress)
        self.worker.signals.log_message.connect(self.log_message)
        self.worker.start()
        
    def start_doc_acquisition(self):
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
        
        self.progress_dialog = QProgressDialog("Acquiring Docs...", "Cancel", 0, 100, self)
        self.progress_dialog.show()
        
        # Choose the appropriate crawling function based on mode
        if "Enhanced" in scraping_mode:
            self.start_worker('acquire_docs', acquire.crawl_docs, urls, settings.DOCS_DIR,
                            max_pages=max_pages, max_depth=max_depth, same_domain_only=same_domain_only)
        else:
            self.start_worker('acquire_docs', acquire.crawl_docs_simple, urls, settings.DOCS_DIR)

    def start_code_scan(self):
        scan_dir = self.scan_dir_entry.text()
        if not scan_dir or not os.path.isdir(scan_dir): return
        
        model_mode = "ollama" if self.model_source_selector.currentText() == "Ollama" else "own_model"
        model_ref = self.ollama_model_selector.currentText() if model_mode == "ollama" else self.own_trained_model
        tokenizer_ref = self.own_tokenizer if model_mode == "own_model" else None
        
        if model_mode == "own_model" and (not model_ref or not tokenizer_ref):
            QMessageBox.warning(self, "Model Not Ready", "Please train or load it first.")
            return

        self.scan_button.setEnabled(False)
        self.start_worker('scan_code', scanner.scan_code, scan_dir, model_mode, model_ref, tokenizer_ref)

    def start_base_training(self):
        self.progress_dialog = QProgressDialog("Training Base Model...", "Cancel", 0, 100, self)
        self.progress_dialog.show()
        self.start_worker('train_lm_base', trainer.train_model, settings.PROCESSED_DATA_DIR, settings.MODEL_SAVE_PATH, finetune=False)
    
    def start_finetuning(self):
        self.progress_dialog = QProgressDialog("Finetuning Model...", "Cancel", 0, 100, self)
        self.progress_dialog.show()
        self.start_worker('train_lm_finetune', trainer.train_model, settings.PROCESSED_DATA_DIR, settings.MODEL_SAVE_PATH, finetune=True)

    @pyqtSlot(object)
    def on_worker_finished(self, result):
        if not self.worker: return
        task = self.worker.task_type
        
        if self.progress_dialog and self.progress_dialog.isVisible(): self.progress_dialog.close()

        if task == 'get_ollama_models':
            self.ollama_model_selector.clear()
            if isinstance(result, list): self.ollama_model_selector.addItems(result)
        elif task == 'scan_code':
            self.scan_button.setEnabled(True)
            self.suggestion_list = result
            summary_text = f"Scan complete. Found {len(self.suggestion_list)} potential issues.\n\n"
            for suggestion in self.suggestion_list[:10]:
                summary_text += f"- {suggestion['description']}\n"
            if len(self.suggestion_list) > 10: summary_text += "- ... and more."
            self.scan_results_text.setPlainText(summary_text)
            if self.suggestion_list:
                self.review_suggestions_button.setEnabled(True)
                self.create_report_button.setEnabled(True)
        elif task == 'get_explanation':
            self.review_suggestions_button.setEnabled(True)
            if self.current_suggestion_index < len(self.suggestion_list):
                suggestion = self.suggestion_list[self.current_suggestion_index]
                dialog = SuggestionDialog(suggestion, result, self)
                dialog_result = dialog.exec()
                if dialog_result == dialog.ApplyCode:
                    preprocess.save_learning_feedback(suggestion, dialog.get_user_justification(), log_message_callback=self.log_message)
                    self.apply_suggestion(suggestion)
                if dialog_result != dialog.CancelAllCode:
                    self.current_suggestion_index += 1
                    if self.current_suggestion_index < len(self.suggestion_list):
                        self.review_next_suggestion()
        elif task == 'generate_report':
            self.create_report_button.setEnabled(True)
            if isinstance(result, tuple) and len(result) == 2:
                md_report, jsonl_data = result
                self.save_report_to_file(md_report)
                self.save_training_data(jsonl_data)
        elif task == 'transcribe_youtube':
            self.transcribe_button.setEnabled(True)
            if isinstance(result, str) and not result.startswith("Error"): self.transcription_results_text.setPlainText(result)
        elif 'acquire' in task or 'preprocess' in task or 'train' in task:
            QMessageBox.information(self, "Success", f"Task '{task}' completed successfully.")
        
        self.worker = None

    def populate_ollama_models(self):
        self.log_message("Refreshing Ollama models...")
        self.start_worker('get_ollama_models', ollama_client.get_ollama_models_list)

    def select_local_corpus_dir(self):
        dir_name = QFileDialog.getExistingDirectory(self, "Select Local Corpus Folder", settings.PROJECT_ROOT)
        if dir_name:
            self.local_files_label.setText(f"Selected: {os.path.basename(dir_name)}")
            settings.DOCS_DIR = dir_name

    def start_preprocessing(self):
        self.progress_dialog = QProgressDialog("Preprocessing...", "Cancel", 0, 100, self)
        self.progress_dialog.show()
        reset_db = self.knowledge_mode_selector.currentText().startswith("Reset")
        # Define paths dynamically to avoid FAISS dependencies
        faiss_index_path = os.path.join(settings.PROCESSED_DATA_DIR, "vector_store.faiss")
        faiss_metadata_path = os.path.join(settings.PROCESSED_DATA_DIR, "vector_store.json")
        self.start_worker('preprocess_docs', preprocess.build_vector_db, settings.DOCS_DIR, faiss_index_path, faiss_metadata_path, reset_db=reset_db)

    def select_scan_directory(self):
        dir_name = QFileDialog.getExistingDirectory(self, "Select Project Directory", settings.PROJECT_ROOT)
        if dir_name: self.scan_dir_entry.setText(dir_name)

    def review_next_suggestion(self):
        if not self.suggestion_list or self.current_suggestion_index >= len(self.suggestion_list):
            QMessageBox.information(self, "Review Complete", "All suggestions reviewed.")
            return
        model_mode = "ollama" if self.model_source_selector.currentText() == "Ollama" else "own_model"
        model_ref = self.ollama_model_selector.currentText() if model_mode == "ollama" else self.own_trained_model
        tokenizer_ref = self.own_tokenizer if model_mode == "own_model" else None
        suggestion = self.suggestion_list[self.current_suggestion_index]
        self.review_suggestions_button.setEnabled(False)
        self.start_worker('get_explanation', ai_tools.get_ai_explanation, suggestion, model_mode, model_ref, tokenizer_ref)

    def apply_suggestion(self, suggestion):
        try:
            filepath, line_number, new_code = suggestion['filepath'], suggestion['line_number'], suggestion['proposed_code']
            with open(filepath, 'r+', encoding='utf-8') as f:
                lines = f.readlines()
                indentation = len(lines[line_number]) - len(lines[line_number].lstrip(' '))
                lines[line_number] = ' ' * indentation + new_code.strip() + '\n'
                f.seek(0)
                f.writelines(lines)
            self.log_message(f"Applied suggestion to {os.path.basename(filepath)} at line {line_number + 1}")
        except Exception as e:
            QMessageBox.critical(self, "Apply Error", f"Could not apply change: {e}")

    def start_youtube_transcription(self):
        youtube_url = self.youtube_url_entry.text()
        if not youtube_url: return
        self.start_worker('transcribe_youtube', ai_tools.transcribe_youtube_tool, youtube_url)

    @pyqtSlot(str)
    def on_worker_error(self, message):
        if self.progress_dialog: self.progress_dialog.close()
        QMessageBox.critical(self, "Worker Error", message)
        logger.error(message)
        self.worker = None

    @pyqtSlot(int, int, str)
    def update_progress(self, current, total, message):
        if self.progress_dialog and self.progress_dialog.isVisible():
            self.progress_dialog.setMaximum(total)
            self.progress_dialog.setValue(current)
            self.progress_dialog.setLabelText(f"{message}")
        elif self.worker and self.worker.task_type == 'scan_code':
            self.scan_progress_bar.setMaximum(total)
            self.scan_progress_bar.setValue(current)
            self.scan_status_label.setText(f"Status: {message}")
    
    @pyqtSlot(str)
    def log_message(self, message):
        self.log_console.append(message)
    
    def start_report_generation(self):
        if not self.suggestion_list: return
        model_mode = "ollama" if self.model_source_selector.currentText() == "Ollama" else "own_model"
        model_ref = self.ollama_model_selector.currentText() if model_mode == "ollama" else self.own_trained_model
        tokenizer_ref = self.own_tokenizer if model_mode == "own_model" else None
        self.start_worker('generate_report', ai_tools.generate_report_and_training_data, self.suggestion_list, model_mode, model_ref, tokenizer_ref)

    def save_report_to_file(self, md_content):
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Markdown Report", "ai_code_review_report.md", "Markdown Files (*.md)")
        if save_path:
            try:
                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write(md_content)
                self.log_message(f"Report saved to {save_path}")
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Could not save report file: {e}")

    def save_training_data(self, jsonl_data):
        if not jsonl_data: return
        try:
            with open(settings.LEARNING_DATA_FILE, 'a', encoding='utf-8') as f:
                f.write(jsonl_data + '\n')
            self.log_message(f"Appended {len(jsonl_data.splitlines())} suggestions to learning data file.")
        except Exception as e:
            self.log_message(f"Error saving training data: {e}")

    def navigate_to_url(self):
        url_text = self.url_bar.text()
        if not url_text.startswith(('http://', 'https://')):
            url_text = 'https://' + url_text
        self.browser.setUrl(QUrl(url_text))

    def update_url_bar(self, qurl):
        self.url_bar.setText(qurl.toString())