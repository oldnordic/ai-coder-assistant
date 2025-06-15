# main_window.py
import sys
import os
import yt_dlp
import requests 
import json     
import torch
from PyQt6.QtWidgets import (QMainWindow, QTabWidget, QApplication, QWidget,
                             QPushButton, QMessageBox, QFileDialog, QProgressDialog,
                             QTextEdit, QVBoxLayout)
from PyQt6.QtCore import QUrl, pyqtSlot, Qt
from PyQt6.QtGui import QIcon

# Import UI setup functions
from browser_tab import setup_browser_tab
from data_tab_widgets import setup_data_tab
from ai_tab_widgets import setup_ai_tab

# Import backend modules
from worker_threads import Worker
from suggestion_dialog import SuggestionDialog
from tokenizers import Tokenizer
import ai_tools
import config
import preprocess_docs
import train_language_model
import ai_coder_scanner
import acquire_docs
import acquire_github
import ollama_client

class AICoderAssistant(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Coder Assistant")
        self.setWindowIcon(QIcon(os.path.join(config.PROJECT_ROOT, 'icon.png')))
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
        
        setup_ai_tab(self.ai_tab, self)
        setup_data_tab(self.data_tab, self)
        setup_browser_tab(self.browser_tab, self)
        
        self.tabs.addTab(self.ai_tab, "AI Agent")
        self.tabs.addTab(self.data_tab, "Data & Training")
        self.tabs.addTab(self.browser_tab, "Browser & Transcription")
        
        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setMaximumHeight(150)
        self.main_layout.addWidget(self.log_console)

        self._connect_signals()
        self.populate_ollama_models()
        self.on_model_source_changed()

    def _connect_signals(self):
        # AI Tab signals
        self.refresh_button.clicked.connect(self.populate_ollama_models)
        self.browse_button.clicked.connect(self.select_scan_directory)
        self.model_source_selector.currentIndexChanged.connect(self.on_model_source_changed)
        self.load_model_button.clicked.connect(self.load_own_trained_model)
        self.scan_button.clicked.connect(self.start_code_scan)
        self.review_suggestions_button.clicked.connect(self.review_next_suggestion)
        self.create_report_button.clicked.connect(self.start_report_generation)
        
        # Data Tab signals
        self.acquire_doc_button.clicked.connect(self.start_doc_acquisition)
        self.acquire_github_button.clicked.connect(self.start_github_acquisition)
        self.add_local_files_button.clicked.connect(self.select_local_corpus_dir)
        self.preprocess_docs_button.clicked.connect(self.start_preprocessing)
        self.train_lm_button.clicked.connect(self.start_base_training)
        self.finetune_lm_button.clicked.connect(self.start_finetuning)
        
        # Browser Tab signals
        self.transcribe_button.clicked.connect(self.start_youtube_transcription)

    def on_model_source_changed(self):
        is_ollama = self.model_source_selector.currentText() == "Ollama"
        self.ollama_model_selector.setVisible(is_ollama)
        self.refresh_button.setVisible(is_ollama)
        self.load_model_button.setVisible(not is_ollama)
        self.model_status_label.setVisible(not is_ollama)
        if not is_ollama:
            self.load_own_trained_model()

    def load_own_trained_model(self):
        model_path = config.MODEL_SAVE_PATH
        tokenizer_path = config.VOCAB_FILE
        if not os.path.exists(model_path) or not os.path.exists(tokenizer_path):
            self.log_message("Own model or tokenizer not found. Please train a model first.")
            self.model_status_label.setText("Status: Model Not Found")
            self.model_status_label.setStyleSheet("color: orange;")
            return
        
        try:
            self.log_message(f"Loading tokenizer from {tokenizer_path}")
            self.own_tokenizer = Tokenizer.from_file(tokenizer_path)
            ntokens = self.own_tokenizer.get_vocab_size()
            
            self.log_message(f"Loading model from {model_path}")
            device = torch.device(config.DEVICE)
            model = train_language_model.TransformerModel(
                ntokens, 
                config.EMBED_DIM, 
                config.NUM_HEADS, 
                config.EMBED_DIM, 
                config.NUM_LAYERS, 
                config.DROPOUT
            ).to(device)
            model.load_state_dict(torch.load(model_path, map_location=device))
            model.eval()
            self.own_trained_model = model
            
            self.log_message("Own trained model loaded successfully.")
            self.model_status_label.setText("Status: Model Loaded")
            self.model_status_label.setStyleSheet("color: lightgreen;")
        except Exception as e:
            self.log_message(f"Failed to load own model: {e}")
            self.model_status_label.setText("Status: Error Loading Model")
            self.model_status_label.setStyleSheet("color: red;")
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
        self.log_message(f"Starting acquisition from {len(urls)} URLs...")
        self.progress_dialog = QProgressDialog("Acquiring Docs...", "Cancel", 0, 100, self)
        self.progress_dialog.show()
        self.start_worker('acquire_docs', acquire_docs.crawl_docs, urls, config.DOCS_DIR)

    def start_github_acquisition(self):
        query = self.github_query_input.text()
        token = self.github_token_input.text()
        if not query:
            QMessageBox.warning(self, "Input Missing", "Please provide a GitHub search query.")
            return
        self.log_message(f"Starting GitHub acquisition for query: '{query}'...")
        self.progress_dialog = QProgressDialog("Acquiring from GitHub...", "Cancel", 0, 100, self)
        self.progress_dialog.show()
        self.start_worker('acquire_github', acquire_github.acquire_github_code, query, config.DOCS_DIR, token)
        
    def start_code_scan(self):
        scan_dir = self.scan_dir_entry.text()
        if not scan_dir or not os.path.isdir(scan_dir):
            QMessageBox.warning(self, "Invalid Directory", "Please select a valid directory to scan.")
            return
        
        model_mode = "ollama" if self.model_source_selector.currentText() == "Ollama" else "own_model"
        model_ref = self.ollama_model_selector.currentText() if model_mode == "ollama" else self.own_trained_model
        tokenizer_ref = self.own_tokenizer if model_mode == "own_model" else None
        
        if model_mode == "own_model" and (not model_ref or not tokenizer_ref):
            QMessageBox.warning(self, "Model Not Ready", "Please train or load your own model first.")
            return

        self.scan_button.setEnabled(False)
        self.review_suggestions_button.setEnabled(False)
        self.create_report_button.setEnabled(False)
        self.start_worker('scan_code', ai_coder_scanner.scan_code, scan_dir, model_mode, model_ref, tokenizer_ref)

    def start_base_training(self):
        self.progress_dialog = QProgressDialog("Training Base Model...", "Cancel", 0, 100, self)
        self.progress_dialog.show()
        self.start_worker('train_lm_base', train_language_model.train_model, config.VOCAB_DIR, config.MODEL_SAVE_PATH, finetune=False)
    
    def start_finetuning(self):
        self.progress_dialog = QProgressDialog("Finetuning Model...", "Cancel", 0, 100, self)
        self.progress_dialog.show()
        self.start_worker('train_lm_finetune', train_language_model.train_model, config.VOCAB_DIR, config.MODEL_SAVE_PATH, finetune=True)

    @pyqtSlot(object)
    def on_worker_finished(self, result):
        if not self.worker: return
        task = self.worker.task_type
        
        if self.progress_dialog and self.progress_dialog.isVisible(): 
            self.progress_dialog.close()

        if task == 'get_ollama_models':
            self.ollama_model_selector.clear()
            if isinstance(result, list):
                self.ollama_model_selector.addItems(result)
            elif isinstance(result, str) and result.startswith("API_ERROR"):
                QMessageBox.warning(self, "Ollama Error", f"Could not fetch models.\n{result}")
        elif task == 'scan_code':
            self.scan_button.setEnabled(True)
            self.suggestion_list = result
            self.current_suggestion_index = 0
            self.scan_results_text.setPlainText(f"Scan complete. Found {len(self.suggestion_list)} issues.")
            if self.suggestion_list:
                self.review_suggestions_button.setEnabled(True)
                self.create_report_button.setEnabled(True)
        elif task == 'get_explanation':
            self.review_suggestions_button.setEnabled(True)
            if self.current_suggestion_index < len(self.suggestion_list):
                suggestion = self.suggestion_list[self.current_suggestion_index]
                explanation = result if isinstance(result, str) else "Could not generate an explanation."
                dialog = SuggestionDialog(suggestion, explanation, self)
                if dialog.exec():
                    if dialog.user_choice == 'apply':
                        self.apply_suggestion(suggestion)
                    self.current_suggestion_index += 1
                    self.review_next_suggestion()
        elif task == 'generate_report':
            self.create_report_button.setEnabled(True)
            if self.suggestion_list:
                self.review_suggestions_button.setEnabled(True)
            if isinstance(result, str) and result:
                self.save_report_to_file(result)
            else:
                self.log_message("Report generation failed or produced an empty report.")
        elif 'acquire' in task or 'preprocess' in task or 'train' in task:
            QMessageBox.information(self, "Success", f"Task '{task}' completed successfully.")
        
        self.worker = None

    def populate_ollama_models(self):
        self.log_message("Refreshing Ollama models...")
        self.start_worker('get_ollama_models', ollama_client.get_ollama_models_list)

    def select_local_corpus_dir(self):
        dir_name = QFileDialog.getExistingDirectory(self, "Select Local Corpus Folder", config.PROJECT_ROOT)
        if dir_name:
            self.local_files_label.setText(f"Selected: {os.path.basename(dir_name)}")
            config.DOCS_DIR = dir_name

    def start_preprocessing(self):
        self.progress_dialog = QProgressDialog("Preprocessing...", "Cancel", 0, 100, self)
        self.progress_dialog.show()
        reset_db = self.knowledge_mode_selector.currentText().startswith("Reset")
        self.start_worker('preprocess_docs', preprocess_docs.build_vector_db, 
                          config.DOCS_DIR, 
                          config.FAISS_INDEX_PATH, 
                          config.FAISS_METADATA_PATH, 
                          reset_db=reset_db)

    def select_scan_directory(self):
        dir_name = QFileDialog.getExistingDirectory(self, "Select Project Directory", config.PROJECT_ROOT)
        if dir_name: self.scan_dir_entry.setText(dir_name)

    def review_next_suggestion(self):
        if not self.suggestion_list or self.current_suggestion_index >= len(self.suggestion_list):
            QMessageBox.information(self, "Review Complete", "All suggestions reviewed.")
            self.review_suggestions_button.setEnabled(False)
            return
        suggestion = self.suggestion_list[self.current_suggestion_index]
        self.review_suggestions_button.setEnabled(False)
        self.start_worker('get_explanation', ai_tools.get_ai_explanation, suggestion)

    def apply_suggestion(self, suggestion):
        try:
            filepath, line_number, new_code = suggestion['filepath'], suggestion['line_number'], suggestion['proposed_code']
            with open(filepath, 'r+', encoding='utf-8') as f:
                lines = f.readlines()
                original_line = lines[line_number]
                indentation = len(original_line) - len(original_line.lstrip(' '))
                lines[line_number] = ' ' * indentation + new_code.strip() + '\n'
                f.seek(0)
                f.writelines(lines)
                f.truncate()
            self.log_message(f"Applied suggestion to {os.path.basename(filepath)} at line {line_number + 1}")
        except Exception as e:
            QMessageBox.critical(self, "Apply Error", f"Could not apply change: {e}")

    def start_youtube_transcription(self):
        youtube_url = self.youtube_url_entry.text()
        if not youtube_url:
            QMessageBox.warning(self, "URL Missing", "Please paste a YouTube URL.")
            return
        self.start_worker('transcribe_youtube', ai_tools.transcribe_youtube_tool, youtube_url)

    @pyqtSlot(str)
    def on_worker_error(self, message):
        if self.progress_dialog and self.progress_dialog.isVisible(): 
            self.progress_dialog.close()
        QMessageBox.critical(self, "Worker Error", message)
        self.log_message(f"Error: {message}")
        self.worker = None

    @pyqtSlot(int, int, str)
    def update_progress(self, current, total, message):
        if self.progress_dialog and self.progress_dialog.isVisible():
            self.progress_dialog.setMaximum(total)
            self.progress_dialog.setValue(current)
            self.progress_dialog.setLabelText(message)
        elif self.worker and self.worker.task_type == 'scan_code':
            self.scan_progress_bar.setMaximum(total)
            self.scan_progress_bar.setValue(current)
            self.scan_status_label.setText(f"Status: {message}")
    
    @pyqtSlot(str)
    def log_message(self, message):
        self.log_console.append(message)
    
    def start_report_generation(self):
        if not self.suggestion_list:
            QMessageBox.warning(self, "No Suggestions", "Please run a scan and generate suggestions first.")
            return

        model_mode = "ollama" if self.model_source_selector.currentText() == "Ollama" else "own_model"
        model_ref = self.ollama_model_selector.currentText() if model_mode == "ollama" else self.own_trained_model
        tokenizer_ref = self.own_tokenizer if model_mode == "own_model" else None
        
        if model_mode == "own_model" and (not model_ref or not tokenizer_ref):
            QMessageBox.warning(self, "Model Not Ready", "Please train or load your own model first before generating a report.")
            return
            
        self.start_worker('generate_report', ai_tools.generate_html_report, 
                          self.suggestion_list, model_mode, model_ref, tokenizer_ref)

    def save_report_to_file(self, html_content):
        save_path, _ = QFileDialog.getSaveFileName(self, "Save HTML Report", "ai_code_review_report.html", "HTML Files (*.html *.htm)")
        if save_path:
            try:
                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                self.log_message(f"Report saved successfully to {save_path}")
                QMessageBox.information(self, "Success", f"Report saved to:\n{save_path}")
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Could not save report file: {e}")

    def navigate_to_url(self):
        url_text = self.url_bar.text()
        if not url_text.startswith(('http://', 'https://')):
            url_text = 'https://' + url_text
        self.browser.setUrl(QUrl(url_text))

    def update_url_bar(self, qurl):
        self.url_bar.setText(qurl.toString())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AICoderAssistant()
    window.show()
    sys.exit(app.exec())