# main_window.py
import sys
import os
import yt_dlp
import requests 
import json     
import torch
from PyQt6.QtWidgets import (QMainWindow, QTabWidget, QApplication, QWidget,
                             QPushButton, QMessageBox, QFileDialog, QProgressDialog)
from PyQt6.QtCore import QUrl, pyqtSlot
from PyQt6.QtGui import QIcon

from browser_tab import setup_browser_tab
from data_tab_widgets import setup_data_tab
from ai_tab_widgets import setup_ai_tab
from worker_threads import Worker
from suggestion_dialog import SuggestionDialog
from tokenizers import Tokenizer
import ai_tools
import config
import preprocess_docs
import train_language_model
import ai_coder_scanner

class AICoderAssistant(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Coder Assistant")
        self.setWindowIcon(QIcon(os.path.join(config.PROJECT_ROOT, 'icon.png')))
        self.setGeometry(100, 100, 1200, 800)
        self.worker = None
        self.progress_dialog = None
        self.scan_report = None
        self.suggestion_list = []
        self.current_suggestion_index = 0
        self.own_trained_model = None
        
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        self.ai_tab = QWidget()
        self.data_tab = QWidget()
        self.browser_tab = QWidget()

        setup_ai_tab(self.ai_tab, self)
        setup_data_tab(self.data_tab, self)
        setup_browser_tab(self.browser_tab, self)

        self.tabs.addTab(self.ai_tab, "AI Agent")
        self.tabs.addTab(self.data_tab, "Data & Training")
        self.tabs.addTab(self.browser_tab, "Browser & Transcription")
        
        self._connect_signals()
        self.populate_ollama_models()

    def _connect_signals(self):
        self.transcribe_button.clicked.connect(self.start_youtube_transcription)
        self.acquire_doc_button.clicked.connect(self.start_doc_acquisition)
        self.acquire_github_button.clicked.connect(self.start_github_acquisition)
        self.add_local_files_button.clicked.connect(self.select_local_corpus_dir)
        self.preprocess_docs_button.clicked.connect(self.start_preprocessing)
        self.train_lm_button.clicked.connect(self.start_training)
        self.finetune_lm_button.clicked.connect(self.start_finetuning)
        
        refresh_button = self.ai_tab.findChild(QPushButton, "Refresh Models")
        if refresh_button: refresh_button.clicked.connect(self.populate_ollama_models)
        
        browse_button = self.ai_tab.findChild(QPushButton, "Browse")
        if browse_button: browse_button.clicked.connect(self.select_scan_directory)

        self.model_source_selector.currentIndexChanged.connect(self.on_model_source_changed)
        self.scan_button.clicked.connect(self.start_code_scan)
        self.review_suggestions_button.clicked.connect(self.review_next_suggestion)
        self.create_report_button.clicked.connect(self.start_report_generation)

    def load_own_trained_model(self):
        """Loads the custom trained PyTorch model and tokenizer from disk."""
        model_path = config.MODEL_SAVE_PATH
        vocab_path = os.path.join(config.VOCAB_DIR, "tokenizer.json")
        
        if not os.path.exists(model_path) or not os.path.exists(vocab_path):
            QMessageBox.warning(self, "Model Not Found", f"Could not find trained model ('{os.path.basename(model_path)}') or tokenizer ('{os.path.basename(vocab_path)}').\nPlease train the model first.")
            return False
        try:
            self.log_message("Loading own trained model...")
            tokenizer = Tokenizer.from_file(vocab_path)
            ntokens = tokenizer.get_vocab_size()
            
            self.own_trained_model = train_language_model.TransformerModel(
                ntokens, config.EMBED_DIM, config.NUM_HEADS, config.EMBED_DIM, 
                config.NUM_LAYERS, config.DROPOUT
            )
            self.own_trained_model.load_state_dict(torch.load(model_path, map_location=config.DEVICE))
            self.own_trained_model.to(config.DEVICE)
            self.own_trained_model.eval()
            self.log_message("Own trained model loaded successfully.")
            return True
        except Exception as e:
            QMessageBox.critical(self, "Model Load Error", f"Failed to load the trained model: {e}")
            self.own_trained_model = None
            return False

    def on_model_source_changed(self):
        source = self.model_source_selector.currentText()
        is_ollama = "Ollama" in source
        self.ollama_model_selector.setEnabled(is_ollama)
        refresh_button = self.ai_tab.findChild(QPushButton, "Refresh Models")
        if refresh_button: refresh_button.setEnabled(is_ollama)
        
        if "Own Trained Model" in source:
            if self.own_trained_model is None:
                if not self.load_own_trained_model():
                    self.model_source_selector.setCurrentText("Use Ollama Model")
        
        self.log_message(f"AI source set to {source}.")

    def start_code_scan(self):
        project_dir = self.scan_dir_entry.text()
        if not os.path.isdir(project_dir):
            QMessageBox.warning(self, "Invalid Directory", "Please select a valid project directory to scan.")
            return
        
        model_source = self.model_source_selector.currentText()
        model_mode, model_ref = "", None

        if "Ollama" in model_source:
            model_mode = "ollama"
            model_ref = self.ollama_model_selector.currentText()
            if not model_ref:
                QMessageBox.warning(self, "Ollama Model Not Selected", "Please select an Ollama model from the dropdown.")
                return
        elif "Own Trained Model" in model_source:
            model_mode = "own_model"
            if self.own_trained_model is None:
                QMessageBox.warning(self, "Model Not Loaded", "The custom model is not loaded. Please re-select 'Use Own Trained Model' or check for errors.")
                return
            model_ref = self.own_trained_model
        
        self.scan_button.setEnabled(False); self.review_suggestions_button.setEnabled(False); self.create_report_button.setEnabled(False)
        self.scan_status_label.setText("Scanning project...")
        self.start_worker('scan_code', ai_coder_scanner.scan_directory_for_errors, project_dir, model_mode, model_ref)

    @pyqtSlot(object)
    def on_worker_finished(self, result):
        finished_worker = self.worker
        if not finished_worker: return
        task = finished_worker.task_type
        self.log_message(f"Worker task '{task}' finished.")
        
        if task == 'scan_code':
            self.scan_button.setEnabled(True)
            if isinstance(result, dict):
                self.scan_report = result
                summary = result.get('report', 'Scan complete.')
                self.scan_results_text.setPlainText(summary)
                self.suggestion_list = []
                self.current_suggestion_index = 0
                for filepath, res_data in result.items():
                    if filepath == 'report' or not isinstance(res_data, dict): continue
                    for proposal in res_data.get('proposals', []):
                        proposal['filepath'] = filepath
                        self.suggestion_list.append(proposal)
                if self.suggestion_list:
                    self.review_suggestions_button.setEnabled(True)
                    self.create_report_button.setEnabled(True)
                    self.log_message(f"Found {len(self.suggestion_list)} suggestions. Click 'Review Suggestions' or 'Create Report'.")
            else:
                self.scan_results_text.setPlainText(f"Scan finished, but returned unexpected data: {result}")
        elif task == 'get_explanation':
            self.review_suggestions_button.setEnabled(True)
            if self.current_suggestion_index < len(self.suggestion_list):
                suggestion = self.suggestion_list[self.current_suggestion_index]
                explanation = result if isinstance(result, str) else "Could not generate an explanation."
                dialog = SuggestionDialog(suggestion, explanation, self)
                dialog.exec()
                user_feedback = dialog.get_user_justification()
                if user_feedback: self.save_learning_feedback(suggestion, user_feedback)
                if dialog.user_choice == 'apply': self.apply_suggestion(suggestion)
                elif dialog.user_choice == 'cancel_all': self.log_message("Suggestion review stopped.")
                else:
                    self.current_suggestion_index += 1
                    self.review_next_suggestion()
        elif task == 'generate_report':
            self.create_report_button.setEnabled(True)
            if self.suggestion_list: self.review_suggestions_button.setEnabled(True)
            if isinstance(result, str) and result:
                self.save_report_to_file(result)
            else:
                QMessageBox.warning(self, "Report Error", "Failed to generate report content.")
        elif task == 'transcribe_youtube':
            self.transcribe_button.setEnabled(True)
            if isinstance(result, str) and not result.startswith("Error"):
                self.transcription_results_text.setPlainText(result)
                self.save_transcription_to_file(result, self.youtube_url_entry.text())
                QMessageBox.information(self, "Success", "Transcription complete.")
            elif result:
                QMessageBox.critical(self, "Transcription Error", str(result))
        elif 'train' in task: # Handles both train_lm and train_lm_finetune
            self.train_lm_button.setEnabled(True)
            self.finetune_lm_button.setEnabled(True)
            if self.progress_dialog: self.progress_dialog.close()
            QMessageBox.information(self, "Success", "Training process complete!")
        elif task == 'preprocess_docs':
            self.preprocess_docs_button.setEnabled(True)
            if self.progress_dialog: self.progress_dialog.close()
            QMessageBox.information(self, "Success", "Preprocessing complete!")
        if self.worker is finished_worker: self.worker = None

    def start_worker(self, task_type, func, *args, **kwargs):
        self.worker = Worker(task_type, func, *args, **kwargs)
        self.worker.signals.finished.connect(self.on_worker_finished)
        self.worker.signals.error.connect(self.on_worker_error)
        self.worker.signals.progress.connect(self.update_progress)
        self.worker.signals.log_message.connect(self.log_message)
        self.worker.start()

    def start_youtube_transcription(self):
        youtube_url = self.youtube_url_entry.text()
        if not youtube_url:
            QMessageBox.warning(self, "URL Missing", "Please paste a YouTube URL in the entry field.")
            return
        self.transcribe_button.setEnabled(False)
        self.transcription_status_label.setText("Starting transcription...")
        self.start_worker('transcribe_youtube', ai_tools.transcribe_youtube_tool, youtube_url)

    def save_transcription_to_file(self, text, url):
        try:
            with yt_dlp.YoutubeDL({'quiet': True, 'noplaylist': True}) as ydl: info_dict = ydl.extract_info(url, download=False)
            video_title = info_dict.get('title', 'youtube_transcription')
            safe_title = "".join([c for c in video_title if c.isalpha() or c.isdigit() or c in (' ', '-')]).rstrip()
            filename = os.path.join(config.DOCS_DIR, f"{safe_title}.txt")
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'w', encoding='utf-8') as f: f.write(text)
            self.log_message(f"Transcription saved to: {filename}")
        except Exception as e: self.log_message(f"Error saving transcription file: {e}")

    def populate_ollama_models(self):
        self.log_message("Refreshing Ollama models...")
        self.ollama_model_selector.clear()
        try:
            response = requests.get(f"{config.OLLAMA_API_BASE_URL}/tags")
            response.raise_for_status()
            models_data = response.json()
            model_names = [model['name'] for model in models_data.get('models', [])]
            if not model_names: self.log_message("No Ollama models found.")
            else:
                self.ollama_model_selector.addItems(model_names)
                self.log_message(f"Found Ollama models: {', '.join(model_names)}")
        except Exception as e: QMessageBox.warning(self, "Ollama Error", f"Could not fetch models. Is Ollama running?\nError: {e}")

    def start_doc_acquisition(self): self.log_message("Doc acquisition not implemented yet.")
    def start_github_acquisition(self): self.log_message("GitHub acquisition not implemented yet.")
        
    def select_local_corpus_dir(self):
        dir_name = QFileDialog.getExistingDirectory(self, "Select Local Corpus Folder", config.PROJECT_ROOT)
        if dir_name:
            self.local_files_label.setText(f"Selected: {dir_name}")
            config.DOCS_DIR = dir_name
            self.log_message(f"Set local corpus directory to: {dir_name}")
            
    def start_preprocessing(self):
        self.preprocess_docs_button.setEnabled(False)
        self.progress_dialog = QProgressDialog("Starting preprocessing...", "Cancel", 0, 100, self)
        self.progress_dialog.setModal(True); self.progress_dialog.canceled.connect(self.cancel_worker); self.progress_dialog.show()
        reset_db = self.knowledge_mode_selector.currentText().startswith("Reset")
        self.start_worker('preprocess_docs', preprocess_docs.build_vector_db, config.DOCS_DIR, config.FAISS_INDEX_PATH, config.FAISS_METADATA_PATH, reset_db=reset_db)

    def start_training(self):
        self.train_lm_button.setEnabled(False)
        self.finetune_lm_button.setEnabled(False)
        self.progress_dialog = QProgressDialog("Starting base model training...", "Cancel", 0, 100, self)
        self.progress_dialog.setModal(True); self.progress_dialog.canceled.connect(self.cancel_worker); self.progress_dialog.show()
        self.start_worker('train_lm', train_language_model.train_model, config.VOCAB_DIR, config.MODEL_SAVE_PATH, finetune=False)
    
    def start_finetuning(self):
        self.train_lm_button.setEnabled(False)
        self.finetune_lm_button.setEnabled(False)
        self.progress_dialog = QProgressDialog("Starting model finetuning...", "Cancel", 0, 100, self)
        self.progress_dialog.setModal(True); self.progress_dialog.canceled.connect(self.cancel_worker); self.progress_dialog.show()
        self.start_worker('train_lm_finetune', train_language_model.train_model, config.VOCAB_DIR, config.MODEL_SAVE_PATH, finetune=True)

    def select_scan_directory(self):
        dir_name = QFileDialog.getExistingDirectory(self, "Select Project Directory to Scan", config.PROJECT_ROOT)
        if dir_name: self.scan_dir_entry.setText(dir_name)

    def review_next_suggestion(self):
        if not self.suggestion_list or self.current_suggestion_index >= len(self.suggestion_list):
            QMessageBox.information(self, "Review Complete", "You have reviewed all available suggestions.")
            self.review_suggestions_button.setEnabled(False)
            return
        suggestion = self.suggestion_list[self.current_suggestion_index]
        self.review_suggestions_button.setEnabled(False)
        self.start_worker('get_explanation', ai_tools.get_ai_explanation, suggestion)

    def apply_suggestion(self, suggestion):
        try:
            filepath, line_number, new_code = suggestion['filepath'], suggestion['line_number'], suggestion['proposed_code']
            with open(filepath, 'r', encoding='utf-8') as f: lines = f.readlines()
            original_line_ending = '\n' if lines[line_number].endswith('\n') else ''
            leading_whitespace = lines[line_number][:len(lines[line_number]) - len(lines[line_number].lstrip())]
            lines[line_number] = leading_whitespace + new_code.strip() + original_line_ending
            with open(filepath, 'w', encoding='utf-8') as f: f.writelines(lines)
            self.log_message(f"Applied suggestion to {os.path.basename(filepath)} at line {line_number + 1}")
            self.current_suggestion_index += 1
            self.review_next_suggestion()
        except Exception as e: QMessageBox.critical(self, "Apply Error", f"Could not apply the change to the file:\n{e}")

    def save_learning_feedback(self, suggestion, user_text):
        if not user_text: return
        feedback_entry = {'issue': suggestion['description'], 'original_code': suggestion['original_code'], 'ai_proposed_code': suggestion['proposed_code'], 'user_feedback_or_code': user_text}
        try:
            os.makedirs(config.LEARNING_DATA_FILE_DIR, exist_ok=True)
            with open(config.LEARNING_DATA_FILE, 'a', encoding='utf-8') as f: f.write(json.dumps(feedback_entry) + '\n')
            self.log_message("Saved user feedback for AI learning.")
        except Exception as e: self.log_message(f"Could not save learning feedback: {e}")

    def cancel_worker(self):
        if self.worker and self.worker.isRunning():
            self.worker.terminate(); self.worker.wait()
            self.log_message("Task canceled by user.")
            self.on_worker_finished(None)

    @pyqtSlot(str)
    def on_worker_error(self, message):
        if not self.worker: return
        task = self.worker.task_type
        if task == 'transcribe_youtube': self.transcribe_button.setEnabled(True)
        elif task == 'preprocess_docs': self.preprocess_docs_button.setEnabled(True)
        elif 'train' in task: self.train_lm_button.setEnabled(True); self.finetune_lm_button.setEnabled(True)
        elif task == 'scan_code': self.scan_button.setEnabled(True)
        elif task == 'get_explanation': self.review_suggestions_button.setEnabled(True)
        elif task == 'generate_report': self.create_report_button.setEnabled(True)
        if self.progress_dialog: self.progress_dialog.close()
        QMessageBox.critical(self, "Worker Error", message)
        self.worker = None

    @pyqtSlot(int, int, str)
    def update_progress(self, current_step, total_steps, message):
        if not self.worker: return
        task = self.worker.task_type
        if task in ['transcribe_youtube', 'scan_code', 'generate_report']:
            bar = self.transcription_progressbar if task == 'transcribe_youtube' else self.scan_progress_bar
            label = self.transcription_status_label if task == 'transcribe_youtube' else self.scan_status_label
            bar.setValue(current_step); bar.setMaximum(total_steps); label.setText(f"Status: {message}")
        elif self.progress_dialog:
            self.progress_dialog.setValue(current_step); self.progress_dialog.setMaximum(total_steps); self.progress_dialog.setLabelText(message)

    @pyqtSlot(str)
    def log_message(self, message):
        print(message)
        self.statusBar().showMessage(str(message), 5000)

    def navigate_to_url(self): self.browser.setUrl(QUrl(self.url_bar.text()))
    def update_url_bar(self, qurl): self.url_bar.setText(qurl.toString())