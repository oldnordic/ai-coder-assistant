;; AI Coder Assistant Emacs Plugin
;; Provides code analysis and security scanning integration

(require 'json)

(defgroup ai-coder nil
  "AI Coder Assistant integration for Emacs"
  :group 'tools)

(defcustom ai-coder-python-path "python"
  "Path to Python executable"
  :type 'string
  :group 'ai-coder)

(defcustom ai-coder-project-path ""
  "Path to AI Coder Assistant project"
  :type 'string
  :group 'ai-coder)

(defcustom ai-coder-enable-auto-scan nil
  "Enable automatic scanning on save"
  :type 'boolean
  :group 'ai-coder)

;; Key bindings
(global-set-key (kbd "C-c a s") 'ai-coder-scan-file)
(global-set-key (kbd "C-c a w") 'ai-coder-scan-workspace)
(global-set-key (kbd "C-c a S") 'ai-coder-security-scan)

;; Commands
(defun ai-coder-scan-file ()
  "Scan current file for code quality issues"
  (interactive)
  (if (string-empty-p ai-coder-project-path)
      (message "Please set ai-coder-project-path")
    (let* ((file-path (buffer-file-name))
           (language (ai-coder-get-language-from-extension (file-name-extension file-path)))
           (command (format "%s -m src.cli.main analyze --file \"%s\" --language %s"
                           ai-coder-python-path file-path language)))
      (ai-coder-run-command command))))

(defun ai-coder-scan-workspace ()
  "Scan entire workspace for code quality issues"
  (interactive)
  (if (string-empty-p ai-coder-project-path)
      (message "Please set ai-coder-project-path")
    (let* ((workspace-path (projectile-project-root))
           (command (format "%s -m src.cli.main scan \"%s\" --output /tmp/emacs_scan_results.json --format json"
                           ai-coder-python-path workspace-path)))
      (ai-coder-run-command command #'ai-coder-display-scan-results))))

(defun ai-coder-security-scan ()
  "Scan workspace for security issues"
  (interactive)
  (if (string-empty-p ai-coder-project-path)
      (message "Please set ai-coder-project-path")
    (let* ((workspace-path (projectile-project-root))
           (command (format "%s -m src.cli.main security-scan \"%s\" --output /tmp/emacs_security_results.json --format json"
                           ai-coder-python-path workspace-path)))
      (ai-coder-run-command command #'ai-coder-display-security-results))))

;; Helper functions
(defun ai-coder-run-command (command &optional callback)
  "Run AI Coder command asynchronously"
  (let ((default-directory ai-coder-project-path))
    (async-shell-command command "*AI-Coder-Output*")
    (when callback
      (run-with-timer 2 nil callback))))

(defun ai-coder-get-language-from-extension (ext)
  "Get language from file extension"
  (let ((language-map
         '(("py" . "python")
           ("js" . "javascript")
           ("ts" . "typescript")
           ("java" . "java")
           ("c" . "c")
           ("cpp" . "cpp")
           ("cs" . "csharp")
           ("go" . "go")
           ("rs" . "rust")
           ("php" . "php")
           ("rb" . "ruby")
           ("swift" . "swift")
           ("kt" . "kotlin")
           ("scala" . "scala")
           ("dart" . "dart")
           ("r" . "r")
           ("m" . "matlab")
           ("sh" . "shell")
           ("sql" . "sql")
           ("html" . "html"))))
    (or (cdr (assoc ext language-map)) "unknown")))

(defun ai-coder-display-scan-results ()
  "Display scan results in a new buffer"
  (let ((results-file "/tmp/emacs_scan_results.json"))
    (if (file-exists-p results-file)
        (let* ((content (with-temp-buffer
                          (insert-file-contents results-file)
                          (buffer-string)))
               (results (json-read-from-string content))
               (formatted (ai-coder-format-results results)))
          (ai-coder-display-results formatted "AI Coder - Scan Results"))
      (message "Scan results not found"))))

(defun ai-coder-display-security-results ()
  "Display security scan results in a new buffer"
  (let ((results-file "/tmp/emacs_security_results.json"))
    (if (file-exists-p results-file)
        (let* ((content (with-temp-buffer
                          (insert-file-contents results-file)
                          (buffer-string)))
               (results (json-read-from-string content))
               (formatted (ai-coder-format-security-results results)))
          (ai-coder-display-results formatted "AI Coder - Security Results"))
      (message "Security scan results not found"))))

(defun ai-coder-display-results (content title)
  "Display results in a new buffer"
  (let ((buffer (get-buffer-create title)))
    (with-current-buffer buffer
      (erase-buffer)
      (insert content)
      (special-mode)
      (goto-char (point-min)))
    (display-buffer buffer)))

(defun ai-coder-format-results (results)
  "Format scan results for display"
  (if (null results)
      "✅ No issues found!\n"
    (let ((output (format "AI Coder Assistant - Scan Results\nFound %d issues\n\n" (length results))))
      (dolist (result results)
        (setq output (concat output
                            (format "File: %s:%s\n" 
                                    (or (cdr (assoc 'file_path result)) "unknown")
                                    (or (cdr (assoc 'line_number result)) "unknown"))
                            (format "Severity: %s\n" (or (cdr (assoc 'severity result)) "unknown"))
                            (format "Type: %s\n" (or (cdr (assoc 'issue_type result)) "unknown"))
                            (format "Description: %s\n" (or (cdr (assoc 'description result)) "No description"))
                            (format "Suggestion: %s\n" (or (cdr (assoc 'suggestion result)) "No suggestion"))
                            "---\n")))
      output)))

(defun ai-coder-format-security-results (results)
  "Format security scan results for display"
  (if (null results)
      "✅ No security issues found!\n"
    (let* ((output (format "AI Coder Assistant - Security Scan Results\nFound %d security issues\n\n" (length results)))
           (critical-count 0)
           (high-count 0))
      (dolist (result results)
        (cond ((string= (cdr (assoc 'severity result)) "critical")
               (setq critical-count (1+ critical-count)))
              ((string= (cdr (assoc 'severity result)) "high")
               (setq high-count (1+ high-count)))))
      (setq output (concat output
                          (format "Critical: %d\n" critical-count)
                          (format "High: %d\n\n" high-count)))
      (when (> critical-count 0)
        (setq output (concat output "🚨 CRITICAL SECURITY ISSUES:\n"))
        (dolist (result results)
          (when (string= (cdr (assoc 'severity result)) "critical")
            (setq output (concat output
                                (format "• %s:%s - %s\n"
                                        (or (cdr (assoc 'file_path result)) "unknown")
                                        (or (cdr (assoc 'line_number result)) "unknown")
                                        (or (cdr (assoc 'description result)) "No description")))))))
      output)))

;; Auto-scan on save (optional)
(when ai-coder-enable-auto-scan
  (add-hook 'after-save-hook 'ai-coder-scan-file))

(provide 'ai-coder) 