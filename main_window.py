import sys, os, logging, traceback, difflib, ast, json, datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel, QTextEdit, QProgressBar, QTabWidget, QGroupBox, QStatusBar, QMessageBox, QDialog, QDialogButtonBox)
from PyQt5.QtCore import (QObject, QThread, pyqtSignal, Qt, QCoreApplication, QTimer)
from PyQt5.QtGui import QTextCursor, QFont, QTextCharFormat
from . import worker_threads as wt, data_tab_widgets, ai_tab_widgets

class SuggestionDialog(QDialog):
    def __init__(self, description, original_code, proposed_code, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI Code Suggestion"); self.setMinimumSize(700, 400)
        layout = QVBoxLayout(self); self.description_label = QLabel(description); self.description_label.setStyleSheet("font-weight: bold;"); layout.addWidget(self.description_label)
        self.diff_text = QTextEdit(); self.diff_text.setReadOnly(True); self.diff_text.setFont(QFont("monospace")); layout.addWidget(self.diff_text)
        diff = difflib.unified_diff(original_code.splitlines(keepends=True), proposed_code.splitlines(keepends=True), fromfile='Original', tofile='Proposed')
        self.diff_text.setText("".join(diff)); self.highlight_diff()
        buttons = QDialogButtonBox(QDialogButtonBox.Apply | QDialogButtonBox.Ignore)
        buttons.button(QDialogButtonBox.Apply).clicked.connect(self.on_apply)
        buttons.button(QDialogButtonBox.Ignore).clicked.connect(self.on_ignore)
        layout.addWidget(buttons)
        
    def highlight_diff(self):
        cursor = self.diff_text.textCursor()
        fmt_add, fmt_rem = QTextCharFormat(), QTextCharFormat()
        fmt_add.setBackground(Qt.darkGreen); fmt_rem.setBackground(Qt.darkRed)
        cursor.movePosition(QTextCursor.Start)
        while not cursor.atEnd():
            cursor.movePosition(QTextCursor.StartOfLine); cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
            line = cursor.selectedText()
            if line.startswith('+') and not line.startswith('+++'): cursor.setCharFormat(fmt_add)
            elif line.startswith('-') and not line.startswith('---'): cursor.setCharFormat(fmt_rem)
            cursor.movePosition(QTextCursor.NextBlock)
            
    def on_apply(self): self.done(QDialog.Accepted)
    def on_ignore(self): self.done(QDialog.Rejected)

class AIFoundryApp(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle("AI Coder Assistant"); self.setGeometry(100, 100, 1200, 800)
        self.current_task, self.thread, self.worker = None, None, None
        self.setup_logging(); self.init_ui()
        QTimer.singleShot(100, self.check_initial_dirs)

    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] - %(message)s", handlers=[logging.FileHandler("application.log")])

    def init_ui(self):
        self.central_widget = QWidget(); self.setCentralWidget(self.central_widget); self.main_layout = QVBoxLayout(self.central_widget)
        self.tabs = QTabWidget(); self.main_layout.addWidget(self.tabs)
        self.data_tab = QWidget(); self.tabs.addTab(self.data_tab, "Data & Training"); data_tab_widgets.setup_data_tab(self.data_tab, self)
        self.ai_tab = QWidget(); self.tabs.addTab(self.ai_tab, "Code Analysis"); ai_tab_widgets.setup_ai_tab(self.ai_tab, self)
        self.log_group = QGroupBox("Application Log"); log_layout = QVBoxLayout(self.log_group)
        self.log_text_edit = QTextEdit(); self.log_text_edit.setReadOnly(True); log_layout.addWidget(self.log_text_edit); self.main_layout.addWidget(self.log_group)
        self.status_bar = self.statusBar()

    def log_message(self, message):
        self.log_text_edit.append(str(message)); logging.info(str(message)); QApplication.processEvents()
        
    def show_error_messagebox(self, title, message):
        QMessageBox.critical(self, title, message); self.log_message(f"ERROR: {title} - {message}")

    def start_worker(self, task_type):
        self.set_ui_busy_state(True, task_type)
        func_to_run, args = None, []
        try:
            from . import config
            if task_type == 'acquire_doc': from . import acquire_docs; func_to_run = acquire_docs.acquire_all_documentation
            elif task_type == 'preprocess_docs':
                from . import preprocess_docs; func_to_run = preprocess_docs.preprocess_documentation_for_ai
                args = [os.path.join(os.getcwd(), config.BASE_DOCS_SAVE_DIR), os.path.join(os.getcwd(), config.PROCESSED_DOCS_DIR), config.CHUNK_SIZE, config.OVERLAP_SIZE, config.VOCAB_SIZE]
            elif task_type == 'train_lm': from . import train_language_model; func_to_run = train_language_model.train_language_model
            elif task_type == 'scan_code':
                from . import ai_coder_scanner; func_to_run = ai_coder_scanner.scan_directory_for_errors
                args = [self.scan_dir_entry.text()]
        except ImportError as e:
            self.log_message(f"Import Error: {e}\n{traceback.format_exc()}"); self.set_ui_busy_state(False); return
            
        self.thread = QThread(); self.worker = wt.Worker(task_type, func_to_run, args, self.log_message, lambda *a: None)
        self.worker.moveToThread(self.thread); self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit); self.worker.finished.connect(self.worker.deleteLater); self.thread.finished.connect(self.thread.deleteLater)
        if task_type == 'scan_code': self.worker.scan_results_signal.connect(self._display_scan_results)
        self.thread.finished.connect(lambda: self.set_ui_busy_state(False)); self.thread.start()

    def check_initial_dirs(self):
        from . import config
        for path in [config.BASE_DOCS_SAVE_DIR, config.PROCESSED_DOCS_DIR]:
            if not os.path.exists(path): os.makedirs(path)

    def _display_scan_results(self, scan_results_dict):
        self.log_message("Scan complete. Presenting proposals...")
        proposals_made = False
        for filepath, result in scan_results_dict.items():
            if result.get("error") or not result.get("proposals"): continue
            try:
                with open(filepath, 'r') as f: original_lines = f.readlines()
            except Exception as e:
                self.log_message(f"Could not open {filepath}: {e}"); continue
            
            proposals_in_file = result.get("proposals", [])
            if proposals_in_file: proposals_made = True

            for proposal in proposals_in_file:
                temp_lines = original_lines[:]; temp_lines[proposal["line_number"]] = proposal["proposed_code"]
                try: ast.parse("".join(temp_lines))
                except (SyntaxError, IndentationError): continue
                
                dialog = SuggestionDialog(f"Suggestion for {os.path.basename(filepath)}", proposal['original_code'], proposal['proposed_code'], self)
                if dialog.exec_() == QDialog.Accepted:
                    try:
                        with open(filepath, 'w') as f: f.writelines(temp_lines)
                        self.log_message(f"APPLIED fix to {os.path.basename(filepath)}."); self._log_learning_experience(filepath, proposal, 'accepted')
                        original_lines = temp_lines
                    except Exception as e: self.log_message(f"FAILED to apply fix to {filepath}: {e}")
                else:
                    self.log_message(f"IGNORED proposal for {os.path.basename(filepath)}."); self._log_learning_experience(filepath, proposal, 'ignored')
        
        self.scan_results_text.setText("Review complete." if proposals_made else "Scan completed: No issues found.")
            
    def _log_learning_experience(self, filepath, proposal, decision):
        from . import config
        record = {"timestamp": datetime.datetime.now().isoformat(), "filepath": filepath, "decision": decision}
        with open(config.LEARNING_DATA_FILE, 'a') as f: f.write(json.dumps(record) + '\n')
        
    def set_ui_busy_state(self, is_busy, task_name=None):
        # A simplified busy state handler
        for button in [self.acquire_doc_button, self.preprocess_docs_button, self.train_lm_button, self.scan_code_button]:
            if button: button.setEnabled(not is_busy)
        if task_name:
            self.status_bar.showMessage(f"Running: {task_name}..." if is_busy else "Task finished.", 5000 if not is_busy else 0)