# main_window.py
import sys, os, logging, difflib, json, datetime

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel, QTextEdit, QProgressBar, QTabWidget, QGroupBox, QStatusBar, QMessageBox, QDialog, QDialogButtonBox, QFileDialog, QCheckBox)
from PyQt6.QtCore import (QThread, pyqtSignal, QCoreApplication, QTimer, QSettings, QUrl, QStandardPaths)
from PyQt6.QtGui import (QSyntaxHighlighter, QTextCharFormat, QColor, QFont)
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage
from PyQt6.QtWebEngineWidgets import QWebEngineView

import worker_threads as wt
import data_tab_widgets
import ai_tab_widgets
import browser_tab
import config
import acquire_docs
import acquire_github
import preprocess_docs
import train_language_model
import ai_coder_scanner
import ollama_client
import ai_tools

import torch 

class DiffHighlighter(QSyntaxHighlighter):
    def __init__(self, parent):
        super().__init__(parent)
        self.fmt_add = QTextCharFormat(); self.fmt_add.setBackground(QColor("#225522")); self.fmt_add.setForeground(QColor("#ffffff"))
        self.fmt_rem = QTextCharFormat(); self.fmt_rem.setBackground(QColor("#882222")); self.fmt_rem.setForeground(QColor("#ffffff"))
    def highlightBlock(self, text):
        if text.startswith('+') and not text.startswith('+++'): self.setFormat(0, len(text), self.fmt_add)
        elif text.startswith('-') and not text.startswith('---'): self.setFormat(0, len(text), self.fmt_rem)

class SuggestionDialog(QDialog):
    def __init__(self, description, original_code, proposed_code, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI Code Suggestion")
        self.setMinimumSize(700, 600)
        
        layout = QVBoxLayout(self)
        self.description_label = QLabel(description); self.description_label.setStyleSheet("font-weight: bold;"); layout.addWidget(self.description_label)
        self.diff_text = QTextEdit(); self.diff_text.setReadOnly(True); self.diff_text.setFont(QFont("monospace"))
        diff = difflib.unified_diff(original_code.splitlines(keepends=True), proposed_code.splitlines(keepends=True), fromfile='Original', tofile='Proposed')
        self.diff_text.setText("".join(diff)); self._diff_highlighter = DiffHighlighter(self.diff_text.document()); layout.addWidget(self.diff_text)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Apply | QDialogButtonBox.StandardButton.Ignore)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); layout.addWidget(buttons)

class AICoderAssistant(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Coder Assistant")
        self.setGeometry(100, 100, 1200, 800)
        self.thread, self.worker, self.current_task = None, None, None
        self.local_corpus_dir = None
        self.scan_proposals_queue = []
        self.setup_logging()
        self.setup_browser_profile()
        self.init_ui() 
        self.load_settings()
        QTimer.singleShot(100, self.check_initial_dirs)
        QTimer.singleShot(200, self.populate_ollama_models)
        self.ai_model_mode = "ollama" # Default mode for scan
        self.own_trained_model = None # To hold your loaded model

    def setup_browser_profile(self):
        profile_path = os.path.join(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation), "browser_profile")
        os.makedirs(profile_path, exist_ok=True)
        self.browser_profile = QWebEngineProfile("persistent_profile", self)
        self.browser_profile.setPersistentStoragePath(profile_path)
        self.browser_profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies)
        self.log_message(f"Browser profile will be stored at: {profile_path}")

    def init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)
        self.data_tab = QWidget()
        self.tabs.addTab(self.data_tab, "Data & Training")
        data_tab_widgets.setup_data_tab(self.data_tab, self) 
        
        self.ai_tab = QWidget()
        self.tabs.addTab(self.ai_tab, "Code Analysis")
        ai_tab_widgets.setup_ai_tab(self.ai_tab, self) 

        # NEW: Connect signals after widgets are guaranteed to exist
        if hasattr(self, 'model_source_selector'): 
            self.model_source_selector.currentIndexChanged.connect(self.on_model_source_changed)
            if self.model_source_selector.currentText() == "Use Own Trained Model":
                self.ollama_model_selector.setEnabled(False)
            else:
                self.ollama_model_selector.setEnabled(True)

        if hasattr(self, 'knowledge_mode_selector'): 
            pass 

        self.browser_ui_tab = QWidget()
        self.tabs.addTab(self.browser_ui_tab, "Browser")
        browser_tab.setup_browser_tab(self.browser_ui_tab, self, self.browser_profile)
        self.log_group = QGroupBox("Application Log")
        log_layout = QVBoxLayout(self.log_group)
        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        log_layout.addWidget(self.log_text_edit)
        self.main_layout.addWidget(self.log_group)
        self.status_bar = self.statusBar()

    def navigate_to_url(self):
        url = self.url_bar.text()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        self.browser.setUrl(QUrl(url))

    def update_url_bar(self, qurl):
        self.url_bar.setText(qurl.toString())
        self.url_bar.setCursorPosition(0)

    def start_youtube_transcription(self):
        youtube_url = self.youtube_url_entry.text()
        if not youtube_url:
            self.show_error_messagebox("Invalid URL", "Please paste a valid YouTube URL.")
            return
        self.log_message(f"Starting transcription for URL: {youtube_url}")
        self.transcription_results_text.setText("Transcription in progress...")
        
        # Pass the URL, the saving callback, and the progress update method
        # The progress callback is update_progress, which is a method of self
        self.start_worker('transcribe_youtube', args=[youtube_url, self._save_transcription_text, self.update_progress]) 
        

    def _display_transcription_result(self, text):
        self.log_message("Transcription finished.")
        self.transcription_results_text.setText(text)

    def _save_transcription_text(self, text, url):
        # Extract a safe filename from the URL
        import re 
        from yt_dlp import YoutubeDL 
        
        video_id_match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
        video_id = video_id_match.group(1) if video_id_match else "unknown_video"
        
        # Get video title using yt-dlp
        title = "Untitled_Video"
        try:
            ydl_opts = {'quiet': True, 'no_warnings': True, 'skip_download': True, 'format': 'bestaudio/best'}
            with YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                title = info_dict.get('title', 'Untitled_Video')
                # Sanitize title for filename
                title = "".join([c for c in title if c.isalnum() or c in (' ', '-', '_')]).rstrip().replace(' ', '_')
                title = title[:50] # Limit title length for filename
        except Exception as e:
            self.log_message(f"Could not get video title for saving: {e}")

        # Construct filename and full path
        filename = f"{title}_{video_id}.txt"
        save_path = os.path.join(config.TRANSCRIPTION_SAVE_DIR, filename)
        
        # Ensure the directory exists
        os.makedirs(config.TRANSCRIPTION_SAVE_DIR, exist_ok=True)

        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(text)
            self.log_message(f"Transcription saved to: {save_path}")
        except Exception as e:
            self.log_message(f"Error saving transcription to file: {e}")
            self.show_error_messagebox("Save Error", f"Failed to save transcription: {e}")


    def setup_logging(self):
        log_file = "application.log"
        logging.basicConfig(level=logging.INFO,
                            format="%(asctime)s [%(levelname)s] - %(message)s",
                            handlers=[logging.FileHandler(log_file, mode='w'), logging.StreamHandler(sys.stdout)])

    def load_settings(self):
        settings = QSettings()
        token = settings.value("github_token", "")
        if hasattr(self, 'github_token_entry'):
            self.github_token_entry.setText(token)
        self.log_message("Settings loaded.")

    def save_settings(self):
        settings = QSettings()
        if hasattr(self, 'github_token_entry'):
            settings.setValue("github_token", self.github_token_entry.text())
        self.log_message("Settings saved.")

    def closeEvent(self, event):
        self.save_settings()
        event.accept()

    def populate_ollama_models(self):
        self.log_message("Refreshing Ollama models...")
        if hasattr(self, 'ollama_model_selector'):
            self.ollama_model_selector.clear()
            self.ollama_model_selector.addItem("Loading...")
            models = ollama_client.list_ollama_models()
            self.ollama_model_selector.clear()
            if isinstance(models, list) and models and "Error" not in models[0]:
                self.ollama_model_selector.addItems(models)
                self.log_message(f"Found Ollama models: {', '.join(models)}")
            else:
                self.ollama_model_selector.addItem("Could not fetch models")
                self.log_message("Ollama service might not be running.")

    def on_model_source_changed(self, index): # NEW method
        selected_text = self.model_source_selector.currentText()
        if selected_text == "Use Ollama Model":
            self.ai_model_mode = "ollama"
            self.ollama_model_selector.setEnabled(True)
            self.log_message("AI source set to Ollama Model.")
        elif selected_text == "Use Own Trained Model":
            self.ai_model_mode = "own_model"
            self.ollama_model_selector.setEnabled(False)
            self.log_message("AI source set to Own Trained Model. Attempting to load model...")
            self.load_own_trained_model()
        
    def load_own_trained_model(self): # NEW method
        if not os.path.exists(config.MODEL_SAVE_PATH):
            self.log_message(f"Error: Own trained model not found at {config.MODEL_SAVE_PATH}.")
            self.show_error_messagebox("Model Not Found", "Your own trained model was not found. Please train it first.")
            self.model_source_selector.setCurrentText("Use Ollama Model") # Revert to Ollama
            self.ollama_model_selector.setEnabled(True) # Re-enable Ollama selector
            return

        try:
            # Need to re-initialize model class with correct vocab size and parameters
            if not os.path.exists(config.VOCAB_FILE):
                self.log_message(f"Error: Vocabulary file not found at {config.VOCAB_FILE}.")
                self.show_error_messagebox("Vocab Not Found", "Vocabulary file needed for your own model was not found.")
                self.model_source_selector.setCurrentText("Use Ollama Model") # Revert to Ollama
                self.ollama_model_selector.setEnabled(True) # Re-enable Ollama selector
                return

            with open(config.VOCAB_FILE, 'r') as f:
                vocab_size = len(json.load(f))

            self.own_trained_model = train_language_model.CoderAILanguageModel(
                vocab_size, config.EMBED_DIM, config.NUM_HEADS, config.NUM_LAYERS, config.DROPOUT
            )
            # Ensure map_location is correct for your system if not CUDA/MPS
            self.own_trained_model.load_state_dict(torch.load(config.MODEL_SAVE_PATH, map_location=torch.device('cpu')))
            self.own_trained_model.eval() # Set to evaluation mode
            self.log_message(f"Own trained model loaded from {config.MODEL_SAVE_PATH}.")
        except Exception as e:
            self.log_message(f"Error loading own trained model: {e}")
            self.show_error_messagebox("Model Load Error", f"Failed to load own trained model: {e}")
            self.own_trained_model = None
            self.model_source_selector.setCurrentText("Use Ollama Model") # Revert on error
            self.ollama_model_selector.setEnabled(True) # Re-enable Ollama selector


    def select_scan_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Project Directory to Scan")
        if directory:
            self.scan_dir_entry.setText(directory)

    def select_local_corpus_dir(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Folder with Local Text/Python Files")
        if directory and hasattr(self, 'local_files_label'):
            self.local_corpus_dir = directory
            self.local_files_label.setText(f"Added: {os.path.basename(directory)}")
            self.log_message(f"Local corpus directory set to: {directory}")

    def log_message(self, message):
        logging.info(str(message))
        if hasattr(self, 'log_text_edit'):
            self.log_text_edit.append(str(message))

    def show_error_messagebox(self, title, message):
        logging.error(f"{title}: {message}")
        QMessageBox.critical(self, title, message)

    def _get_ui_widgets_for_task(self, task_name):
        return {
            'acquire_doc': (self.acquire_doc_progressbar, self.acquire_doc_status_label),
            'acquire_github': (self.github_progressbar, self.github_status_label),
            'preprocess_docs': (self.preprocess_docs_progressbar, self.preprocess_docs_status_label),
            'train_lm': (self.train_lm_progressbar, self.train_lm_status_label),
            'scan_code': (self.scan_progress_bar, self.scan_status_label),
            'transcribe_youtube': (self.transcription_progressbar, self.transcription_status_label) # Corrected: Added transcription widgets
        }.get(task_name, (None, None))

    def handle_worker_error(self, title, message):
        self.show_error_messagebox(title, message)
        _, status_label = self._get_ui_widgets_for_task(self.current_task)
        if status_label:
            status_label.setText("Error!")
            status_label.setStyleSheet("color: red;")
        self.set_ui_busy_state(False)

    def start_worker(self, task_type, args=None):
        if self.thread and self.thread.isRunning():
            self.show_error_messagebox("Task in Progress", "A task is already running."); return
        
        self.current_task = task_type
        if task_type == 'scan_code':
            self.scan_results_text.clear()
            self.review_suggestions_button.setEnabled(False)
            self.review_suggestions_button.setText("Review Suggestions")

        progress_bar, status_label = self._get_ui_widgets_for_task(self.current_task)
        if status_label: status_label.setStyleSheet(""); status_label.setText("Starting...")
        if progress_bar: progress_bar.setValue(0) # Reset progress bar for new task
        
        self.set_ui_busy_state(True)
        
        try:
            if task_type == 'acquire_doc':
                selected_language = self.doc_language_selector.currentText()
                func_to_run = acquire_docs.acquire_docs_for_language
                effective_args = [selected_language]
            elif task_type == 'acquire_github':
                token = self.github_token_entry.text()
                if not token: raise ValueError("GitHub Token is missing.")
                func_to_run = acquire_github.search_and_download_github_code
                effective_args = [self.github_query_entry.text(), token, os.path.join(config.BASE_DOCS_SAVE_DIR, "github_code")]
            elif task_type == 'preprocess_docs':
                func_to_run = preprocess_docs.preprocess_documentation_for_ai
                # Get the selected accumulation mode
                accumulation_mode = self.knowledge_mode_selector.currentText()
                self.log_message(f"Starting preprocessing in '{accumulation_mode}' mode.")
                effective_args = [config.BASE_DOCS_SAVE_DIR, self.local_corpus_dir, accumulation_mode] # Pass mode
            elif task_type == 'train_lm':
                func_to_run, effective_args = train_language_model.train_language_model, []
            elif task_type == 'transcribe_youtube':
                func_to_run = ai_tools.transcribe_youtube_tool
                # args passed from start_youtube_transcription are [youtube_url, self._save_transcription_text, self.update_progress]
                if args is None or len(args) < 3: 
                    raise ValueError("Missing arguments for transcribe_youtube_tool: [youtube_url, save_callback, progress_callback]")
                effective_args = args # Pass the args list directly, which contains URL, save_callback, and progress_callback
            elif task_type == 'scan_code':
                scan_dir = self.scan_dir_entry.text()
                if not os.path.isdir(scan_dir): raise ValueError(f"Invalid scan directory: {scan_dir}")
                # Pass both the scan directory AND the selected model source/name
                if self.ai_model_mode == "ollama":
                    selected_ollama_model = self.ollama_model_selector.currentText()
                    func_to_run, effective_args = ai_coder_scanner.scan_directory_for_errors, [scan_dir, self.ai_model_mode, selected_ollama_model]
                elif self.ai_model_mode == "own_model":
                    if self.own_trained_model is None:
                        raise ValueError("Own trained model is not loaded. Please train/load it first.")
                    # When using own model, pass the model instance directly
                    func_to_run, effective_args = ai_coder_scanner.scan_directory_for_errors, [scan_dir, self.ai_model_mode, self.own_trained_model]
                else:
                    raise ValueError("Invalid AI model mode selected.")
            else:
                raise ValueError(f"Unknown task type: {task_type}")

            self.thread = QThread()
            self.worker = wt.Worker(task_type, func_to_run, effective_args)
            self.worker.moveToThread(self.thread)
            
            self.thread.started.connect(self.worker.run)
            self.worker.log_message.connect(self.log_message)
            self.worker.error_signal.connect(self.handle_worker_error)
            self.worker.progress.connect(self.update_progress) # Corrected: progress signal connected here
            self.worker.finished.connect(self._on_worker_finished)
            
            if task_type == 'scan_code': self.worker.scan_results_signal.connect(self._display_scan_report)
            if task_type == 'transcribe_youtube': 
                self.worker.transcription_finished.connect(self._display_transcription_result)
                
        except Exception as e:
            self.show_error_messagebox("Task Error", str(e)); self.set_ui_busy_state(False)

    def update_progress(self, current_step, total_steps, message):
        progress_bar, status_label = self._get_ui_widgets_for_task(self.current_task)
        if progress_bar and status_label:
            # For indeterminate progress, set range to 0,0 and message
            if total_steps == 0:
                progress_bar.setRange(0, 0)
                progress_bar.setValue(0) # Keep at 0 for visual effect
            else:
                progress_bar.setRange(0, total_steps)
                progress_bar.setValue(current_step)
            status_label.setText(message)
        QApplication.processEvents() # Process events to ensure UI updates


    def _on_worker_finished(self):
        self.set_ui_busy_state(False)
        self.log_message(f"--- Task '{self.current_task}' finished. ---")
        
        # Reset progress bar and status for the finished task to "Ready" or 0%
        progress_bar, status_label = self._get_ui_widgets_for_task(self.current_task)
        if progress_bar and status_label:
            progress_bar.setRange(0, 100) # Reset to a determinate range
            progress_bar.setValue(0)     # Set to 0%
            status_label.setText("Ready") # Set status to Ready
            status_label.setStyleSheet("") # Clear any error styling

        if self.thread:
            self.thread.quit()
            self.thread.wait()
        self.thread = self.worker = self.current_task = None

    def check_initial_dirs(self):
        for path in [config.BASE_DOCS_SAVE_DIR, config.PROCESSED_DOCS_DIR, config.LEARNING_DATA_FILE_DIR, config.TRANSCRIPTION_SAVE_DIR]:
            if not os.path.exists(path):
                os.makedirs(path); self.log_message(f"Created directory: {path}")

    def _display_scan_report(self, scan_results_dict):
        report_content = scan_results_dict.pop("report", "### Error: Report not generated. ###")
        self.scan_results_text.setMarkdown(report_content)
        
        self.scan_proposals_queue = []
        for filepath, result in scan_results_dict.items():
            if result.get("proposals"):
                for proposal in result["proposals"]:
                    proposal['filepath'] = filepath
                    self.scan_proposals_queue.append(proposal)

        if self.scan_proposals_queue:
            self.review_suggestions_button.setEnabled(True)
            self.review_suggestions_button.setText(f"Review Suggestions ({len(self.scan_proposals_queue)} left)")
            self.log_message(f"Scan complete. {len(self.scan_proposals_queue)} suggestions ready for review.")
        else:
            self.review_suggestions_button.setEnabled(False)
            self.log_message("Scan complete. No suggestions to review.")

    def review_next_suggestion(self):
        if not self.scan_proposals_queue:
            self.show_error_messagebox("Review Complete", "No more suggestions to review.")
            self.review_suggestions_button.setEnabled(False)
            return

        proposal = self.scan_proposals_queue.pop(0)
        filepath = proposal['filepath']
        filename = os.path.basename(filepath)
        
        dialog = SuggestionDialog(
            f"Suggestion for {filename} (Line: {proposal['line_number'] + 1})",
            proposal['original_code'],
            proposal['proposed_code'],
            self
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._apply_and_log_change(proposal)
        else:
            self.log_message(f"Rejected suggestion for {filepath}")
            self._log_learning_experience(filepath, proposal, 'rejected')
        
        remaining = len(self.scan_proposals_queue)
        if remaining > 0:
            self.review_suggestions_button.setText(f"Review Suggestions ({remaining} left)")
        else:
            self.review_suggestions_button.setText("Review Complete")
            self.review_suggestions_button.setEnabled(False)

    def _apply_and_log_change(self, proposal):
        filepath = proposal['filepath']
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            lines[proposal['line_number']] = proposal['proposed_code'] + '\n'

            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            self.log_message(f"APPLIED fix to {os.path.basename(filepath)}.")
            self._log_learning_experience(filepath, proposal, 'accepted')
        except Exception as e:
            self.show_error_messagebox("File Write Error", f"Could not write changes to {filepath}: {e}")
        
    def _log_learning_experience(self, filepath, proposal, decision):
        record = {"timestamp": datetime.datetime.now().isoformat(), "filepath": filepath, "decision": decision, "proposal": proposal}
        learning_file = os.path.join(config.LEARNING_DATA_FILE_DIR, "learning_data.jsonl")
        try:
            with open(learning_file, 'a') as f: f.write(json.dumps(record) + '\n')
        except IOError as e:
            self.log_message(f"Could not write to learning log: {e}")

    def set_ui_busy_state(self, is_busy):
        buttons = [
            self.acquire_doc_button, self.acquire_github_button, self.add_local_files_button,
            self.preprocess_docs_button, self.train_lm_button, getattr(self, 'scan_button', None), 
            getattr(self, 'browse_button', None), getattr(self, 'transcribe_button', None),
            self.review_suggestions_button
        ]
        for button in buttons:
            if button:
                if button == self.review_suggestions_button:
                    if not is_busy and self.scan_proposals_queue:
                        button.setEnabled(True)
                    else:
                        button.setEnabled(False)
                else:
                    button.setEnabled(not is_busy)
        
        if hasattr(self, 'status_bar'):
            if is_busy and self.current_task:
                self.status_bar.showMessage(f"Running: {self.current_task}...")
            else:
                self.status_bar.showMessage("Ready", 5000)
                self.status_bar.showMessage("Ready", 5000)