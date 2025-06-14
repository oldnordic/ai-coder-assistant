# worker_threads.py
from PyQt6.QtCore import QObject, pyqtSignal, QThread
import traceback
import sys

class Worker(QObject):
    finished = pyqtSignal()
    error_signal = pyqtSignal(str, str) # title, message
    progress = pyqtSignal(int, int, str)
    log_message = pyqtSignal(str)
    
    # Specific signals for task results
    scan_results_signal = pyqtSignal(dict)
    transcription_finished = pyqtSignal(str) # Emits the transcription text

    def __init__(self, task_type, func, args, kwargs=None):
        super().__init__()
        self.task_type = task_type
        self.func = func
        self.args = args if args is not None else []
        self.kwargs = kwargs if kwargs is not None else {}

    def run(self):
        try:
            # Inject callbacks into kwargs, or ensure they are passed correctly via args
            # The transcribe_youtube_tool explicitly expects saving_callback and log_message_callback
            if self.task_type == 'transcribe_youtube':
                # original args from main_window: [youtube_url, self._save_transcription_text, self.update_progress]
                # self.func (ai_tools.transcribe_youtube_tool) needs: youtube_url, saving_callback, log_message_callback, progress_callback
                
                youtube_url_arg = self.args[0]
                saving_callback_arg = self.args[1]
                progress_callback_arg = self.args[2] # Correctly retrieve the third argument
                
                # Call the transcribe_youtube_tool with all necessary arguments
                # The _log parameter for transcribe_youtube_tool is now provided by self.log_message.emit
                result = self.func(youtube_url_arg, saving_callback_arg, self.log_message.emit, progress_callback_arg) # Pass progress_callback_arg
                
                # Emit the transcription result for UI display
                self.transcription_finished.emit(result) 
                
            elif self.task_type == 'scan_code':
                # For scan_code, self.func (ai_coder_scanner.scan_directory_for_errors)
                # needs: scan_dir, model_mode, model_ref, log_message_callback, progress_callback
                # The worker automatically connects log_message and progress via signals
                scan_dir_arg = self.args[0]
                model_mode_arg = self.args[1]
                model_ref_arg = self.args[2]

                results_dict = self.func(
                    scan_dir=scan_dir_arg,
                    model_mode=model_mode_arg,
                    model_ref=model_ref_arg,
                    log_message_callback=self.log_message.emit,
                    progress_callback=self.progress.emit
                )
                self.scan_results_signal.emit(results_dict)
            
            # General case for other tasks that don't need special callback injection
            elif self.task_type == 'preprocess_docs':
                # preprocess_docs.build_vector_db needs: base_raw_docs_dir, local_additional_docs_dir, accumulation_mode, progress_callback, log_message_callback
                base_dir = self.args[0]
                local_dir = self.args[1]
                mode = self.args[2]
                self.func(
                    base_raw_docs_dir=base_dir,
                    local_additional_docs_dir=local_dir,
                    accumulation_mode=mode,
                    progress_callback=self.progress.emit,
                    log_message_callback=self.log_message.emit
                )
            elif self.task_type == 'train_lm':
                # train_language_model.train_language_model needs: progress_callback, log_message_callback
                self.func(
                    progress_callback=self.progress.emit,
                    log_message_callback=self.log_message.emit
                )
            elif self.task_type == 'acquire_doc':
                # acquire_docs.acquire_docs_for_language needs: language, progress_callback, log_message_callback
                lang = self.args[0]
                self.func(
                    language=lang,
                    progress_callback=self.progress.emit,
                    log_message_callback=self.log_message.emit
                )
            elif self.task_type == 'acquire_github':
                # acquire_github.search_and_download_github_code needs: query, token, save_dir, progress_callback, log_message_callback
                query, token, save_dir = self.args[0], self.args[1], self.args[2]
                self.func(
                    query=query,
                    token=token,
                    save_dir=save_dir,
                    progress_callback=self.progress.emit,
                    log_message_callback=self.log_message.emit
                )

            # Fallback for any other generic function call if not explicitly handled above
            # This is less robust than specific handling for each task.
            else:
                self.log_message.emit(f"Worker running generic task: {self.task_type} with args: {self.args}")
                # Try to pass log_message_callback and progress_callback if function signature supports it
                try:
                    result = self.func(
                        *self.args, 
                        log_message_callback=self.log_message.emit, 
                        progress_callback=self.progress.emit, 
                        **self.kwargs
                    )
                    if self.task_type == 'transcribe_youtube' and isinstance(result, str):
                         self.transcription_finished.emit(result)
                except TypeError as te:
                    # If the function doesn't accept these callbacks, call without them
                    self.log_message.emit(f"Warning: Generic task {self.task_type} does not accept std callbacks. Trying without. Error: {te}")
                    result = self.func(*self.args, **self.kwargs)
                    if self.task_type == 'transcribe_youtube' and isinstance(result, str):
                         self.transcription_finished.emit(result)


        except Exception as e:
            ex_type, ex_value, ex_traceback = sys.exc_info()
            error_message = f"Error in '{self.task_type}' task:\n"
            error_message += "".join(traceback.format_exception(ex_type, ex_value, ex_traceback))
            self.error_signal.emit(f"Error in '{self.task_type}' task", error_message)
        finally:
            self.finished.emit()