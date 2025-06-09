import sys, os, logging, traceback, difflib, ast, json, datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel, QTextEdit, QProgressBar, QTabWidget, QGroupBox, QStatusBar, QMessageBox, QDialog, QDialogButtonBox, QFileDialog)
from PyQt5.QtCore import (QObject, QThread, pyqtSignal, Qt, QCoreApplication, QTimer, QSettings)
from PyQt5.QtGui import QTextCursor, QFont, QTextCharFormat
import worker_threads as wt
import data_tab_widgets
import ai_tab_widgets
import config
import acquire_docs
import acquire_github
import preprocess_docs
import train_language_model
import ai_coder_scanner

class SuggestionDialog(QDialog):
    # ... (This class is unchanged) ...
    def __init__(self, description, original_code, proposed_code, parent=None):
        super().__init__(parent);self.setWindowTitle("AI Code Suggestion");self.setMinimumSize(700, 400);layout=QVBoxLayout(self);self.description_label=QLabel(description);self.description_label.setStyleSheet("font-weight: bold;");layout.addWidget(self.description_label);self.diff_text=QTextEdit();self.diff_text.setReadOnly(True);self.diff_text.setFont(QFont("monospace"));layout.addWidget(self.diff_text);diff=difflib.unified_diff(original_code.splitlines(keepends=True), proposed_code.splitlines(keepends=True), fromfile='Original', tofile='Proposed');self.diff_text.setText("".join(diff));self.highlight_diff();buttons=QDialogButtonBox(QDialogButtonBox.Apply | QDialogButtonBox.Ignore);buttons.button(QDialogButtonBox.Apply).clicked.connect(self.on_apply);buttons.button(QDialogButtonBox.Ignore).clicked.connect(self.on_ignore);layout.addWidget(buttons)
    def highlight_diff(self):
        cursor = self.diff_text.textCursor();fmt_add, fmt_rem = QTextCharFormat(), QTextCharFormat();fmt_add.setBackground(Qt.darkGreen);fmt_rem.setBackground(Qt.darkRed);cursor.movePosition(QTextCursor.Start);
        while not cursor.atEnd():
            cursor.movePosition(QTextCursor.StartOfLine);cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor);line = cursor.selectedText()
            if line.startswith('+') and not line.startswith('+++'): cursor.setCharFormat(fmt_add)
            elif line.startswith('-') and not line.startswith('---'): cursor.setCharFormat(fmt_rem)
            cursor.movePosition(QTextCursor.NextBlock)
    def on_apply(self): self.done(QDialog.Accepted)
    def on_ignore(self): self.done(QDialog.Rejected)

class AIFoundryApp(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle("AI Coder Assistant"); self.setGeometry(100, 100, 1200, 800)
        self.thread, self.worker, self.current_task = None, None, None
        self.local_corpus_dir = None
        self.setup_logging(); self.init_ui()
        self.load_settings()
        QTimer.singleShot(100, self.check_initial_dirs)

    def setup_logging(self):
        log_file = "application.log"
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        if logger.hasHandlers(): logger.handlers.clear()
        file_handler = logging.FileHandler(log_file, mode='w')
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] - %(message)s")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    def load_settings(self):
        settings = QSettings()
        token = settings.value("github_token", "")
        if token:
            self.github_token_entry.setText(token)
            self.log_message("Loaded saved GitHub token.")

    def save_settings(self):
        settings = QSettings()
        token = self.github_token_entry.text()
        settings.setValue("github_token", token)
        self.log_message("Settings saved.")

    def closeEvent(self, event):
        self.save_settings()
        event.accept()

    def init_ui(self):
        self.central_widget = QWidget(); self.setCentralWidget(self.central_widget); self.main_layout = QVBoxLayout(self.central_widget)
        self.tabs = QTabWidget(); self.main_layout.addWidget(self.tabs)
        self.data_tab = QWidget(); self.tabs.addTab(self.data_tab, "Data & Training"); data_tab_widgets.setup_data_tab(self.data_tab, self)
        self.ai_tab = QWidget(); self.tabs.addTab(self.ai_tab, "Code Analysis"); ai_tab_widgets.setup_ai_tab(self.ai_tab, self)
        self.log_group = QGroupBox("Application Log"); log_layout = QVBoxLayout(self.log_group)
        self.log_text_edit = QTextEdit(); self.log_text_edit.setReadOnly(True); log_layout.addWidget(self.log_text_edit); self.main_layout.addWidget(self.log_group)
        self.status_bar = self.statusBar()

    def select_local_corpus_dir(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Folder with Local Text/Python Files")
        if directory:
            self.local_corpus_dir = directory
            self.local_files_label.setText(f"Added: {os.path.basename(directory)}")
            self.log_message(f"Local corpus directory set to: {directory}")

    def log_message(self, message):
        """NEW: This function is now safer and does not cause a recursive loop."""
        self.log_text_edit.append(str(message))
        logging.info(str(message))
        # The line below was the cause of the crash and has been removed.
        # QApplication.processEvents() 
        
    def show_error_messagebox(self, title, message):
        self.log_message(f"ERROR: {title} - {message}")
        QMessageBox.critical(self, title, message)

    def _get_ui_widgets_for_task(self, task_name):
        task_map = {
            'acquire_doc': (self.acquire_doc_progressbar, self.acquire_doc_status_label),
            'acquire_github': (self.github_progressbar, self.github_status_label),
            'preprocess_docs': (self.preprocess_docs_progressbar, self.preprocess_docs_status_label),
            'train_lm': (self.train_lm_progressbar, self.train_lm_status_label),
            'scan_code': (self.scan_progress_bar, self.scan_status_label)
        }
        return task_map.get(task_name, (None, None))

    def handle_worker_error(self, title, message):
        self.show_error_messagebox(title, message)
        _ , status_label = self._get_ui_widgets_for_task(self.current_task)
        if status_label:
            status_label.setText("Error!")
            status_label.setStyleSheet("color: red;")

    def start_worker(self, task_type):
        if self.thread and self.thread.isRunning():
            self.show_error_messagebox("Task in Progress", "A task is already running. Please wait for it to complete.")
            return

        self.current_task = task_type
        progress_bar, status_label = self._get_ui_widgets_for_task(task_type)
        if status_label: status_label.setStyleSheet(""); status_label.setText("Starting...")
        if progress_bar: progress_bar.setValue(0)
            
        self.set_ui_busy_state(True, task_type)
        func_to_run, args = None, []
        try:
            if task_type == 'acquire_doc': func_to_run = acquire_docs.acquire_all_documentation
            elif task_type == 'acquire_github':
                func_to_run = acquire_github.search_and_download_github_code
                token = self.github_token_entry.text()
                if not token: self.show_error_messagebox("Missing Token", "Please provide a GitHub Personal Access Token."); self.set_ui_busy_state(False); return
                query = self.github_query_entry.text()
                save_dir = os.path.join(config.BASE_DOCS_SAVE_DIR, "github_code")
                args = [query, token, save_dir]
            elif task_type == 'preprocess_docs':
                func_to_run = preprocess_docs.preprocess_documentation_for_ai
                args = [config.BASE_DOCS_SAVE_DIR, config.PROCESSED_DOCS_DIR, config.CHUNK_SIZE, config.OVERLAP_SIZE, config.VOCAB_SIZE, self.local_corpus_dir]
            elif task_type == 'train_lm': func_to_run = train_language_model.train_language_model
            elif task_type == 'scan_code':
                scan_dir = self.scan_dir_entry.text()
                if not os.path.isdir(scan_dir): self.show_error_messagebox("Invalid Directory", f"The directory '{scan_dir}' does not exist."); self.set_ui_busy_state(False); return
                func_to_run = ai_coder_scanner.scan_directory_for_errors
                args = [scan_dir]
        except Exception as e:
            logging.error(f"Error preparing task '{task_type}': {e}\n{traceback.format_exc()}")
            self.show_error_messagebox("Task Error", f"Could not prepare task '{task_type}'.")
            self.set_ui_busy_state(False)
            return

        self.thread = QThread()
        self.worker = wt.Worker(task_type, func_to_run, args)
        self.worker.moveToThread(self.thread)
        
        self.thread.started.connect(self.worker.run)
        self.worker.log_message.connect(self.log_message)
        self.worker.error_signal.connect(self.handle_worker_error)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self._on_worker_finished)

        if task_type == 'scan_code': self.worker.scan_results_signal.connect(self._display_scan_results)
        self.thread.start()

    def update_progress(self, current_step, total_steps, message):
        self.log_message(f"UI Update: {message} ({current_step}/{total_steps})")
        progress_bar, status_label = self._get_ui_widgets_for_task(self.current_task)
        if progress_bar and status_label:
            if total_steps > 0: progress_bar.setRange(0, total_steps); progress_bar.setValue(current_step)
            else: progress_bar.setRange(0, 0)
            status_label.setText(message)
        # This call is still useful here to keep the UI smooth during intensive updates
        QApplication.processEvents() 

    def _on_worker_finished(self):
        self.set_ui_busy_state(False)
        self.log_message(f"--- Task '{self.current_task}' finished. ---")
        self.thread, self.worker, self.current_task = None, None, None

    def check_initial_dirs(self):
        for path in [config.BASE_DOCS_SAVE_DIR, config.PROCESSED_DOCS_DIR]:
            if not os.path.exists(path):
                try: os.makedirs(path); self.log_message(f"Created directory: {path}")
                except OSError as e: self.show_error_messagebox("Directory Creation Failed", f"Could not create directory '{path}': {e}")

    def _display_scan_results(self, scan_results_dict):
        if "Error" in scan_results_dict: self.show_error_messagebox("Scan Error", scan_results_dict["Error"]); self.scan_results_text.setText(f"Scan failed: {scan_results_dict['Error']}"); return
        if "Info" in scan_results_dict: self.log_message(scan_results_dict["Info"]); self.scan_results_text.setText(scan_results_dict["Info"]); return
        total_files_scanned = len(scan_results_dict); self.log_message(f"Scan complete. Reviewing results from {total_files_scanned} scanned files...")
        proposals_made = False
        for filepath, result in scan_results_dict.items():
            if result.get("error") or not result.get("proposals"): continue
            try:
                with open(filepath, 'r', encoding='utf-8') as f: original_lines = f.readlines()
            except Exception as e: self.log_message(f"Could not open {filepath}: {e}"); continue
            proposals_in_file = result.get("proposals", []);
            if proposals_in_file: proposals_made = True
            for proposal in proposals_in_file:
                line_num = proposal.get("line_number", -1)
                if not (0 <= line_num < len(original_lines)): continue
                temp_lines = original_lines[:]; temp_lines[line_num] = proposal["proposed_code"]
                try: ast.parse("".join(temp_lines))
                except (SyntaxError, IndentationError) as e: self.log_message(f"Skipping proposal for {os.path.basename(filepath)} due to syntax error: {e}"); continue
                dialog = SuggestionDialog(f"Suggestion for {os.path.basename(filepath)}", proposal['original_code'], proposal['proposed_code'], self)
                if dialog.exec_() == QDialog.Accepted:
                    try:
                        with open(filepath, 'w', encoding='utf-8') as f: f.writelines(temp_lines)
                        self.log_message(f"APPLIED fix to {os.path.basename(filepath)}."); self._log_learning_experience(filepath, proposal, 'accepted'); original_lines = temp_lines
                    except Exception as e: self.log_message(f"FAILED to apply fix to {filepath}: {e}"); self.show_error_messagebox("File Write Error", f"Could not write changes to {filepath}.")
                else: self.log_message(f"IGNORED proposal for {os.path.basename(filepath)}."); self._log_learning_experience(filepath, proposal, 'ignored')
        final_text = "Review complete." if proposals_made else "Scan completed: No issues found."
        final_text += f"\n\nTotal Python files scanned: {total_files_scanned}."
        self.scan_results_text.setText(final_text)

    def _log_learning_experience(self, filepath, proposal, decision):
        record = {"timestamp": datetime.datetime.now().isoformat(), "filepath": filepath, "decision": decision, "proposal": proposal}
        try:
            with open(config.LEARNING_DATA_FILE, 'a') as f: f.write(json.dumps(record) + '\n')
        except IOError as e: self.log_message(f"Could not write to learning log: {e}")

    def set_ui_busy_state(self, is_busy, task_name=None):
        buttons = [getattr(self, name, None) for name in ["acquire_doc_button", "acquire_github_button", "add_local_files_button", "preprocess_docs_button", "train_lm_button", "scan_code_button", "browse_dir_button"]]
        for button in buttons:
            if button: button.setEnabled(not is_busy)
        if is_busy and task_name: self.status_bar.showMessage(f"Running: {task_name}...")
        else: self.status_bar.showMessage("Ready", 5000)