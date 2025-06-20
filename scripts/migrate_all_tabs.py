#!/usr/bin/env python3
"""
Comprehensive Migration Script for AI Coder Assistant
Migrates all QThread subclasses to use the centralized ThreadManager pattern.
"""

import os
import re
import shutil
from pathlib import Path

# Configuration
UI_DIR = "src/frontend/ui"
BACKUP_DIR = "backup_before_migration"

# Migration templates for different types of operations
MIGRATION_TEMPLATES = {
    "analysis": """
# Backend function for ThreadManager
def {operation_name}_backend({params}, progress_callback=None, log_callback=None, cancellation_callback=None):
    \"\"\"Backend function for {operation_description}.\"\"\"
    try:
        if progress_callback:
            progress_callback(1, 3, "Starting {operation_description}...")
        
        if cancellation_callback and cancellation_callback():
            return None
        
        # TODO: Implement actual {operation_description} logic here
        # Replace this with your actual backend logic
        
        if progress_callback:
            progress_callback(2, 3, "Processing results...")
        
        if cancellation_callback and cancellation_callback():
            return None
        
        # TODO: Return actual results
        result = {{"success": True, "data": "placeholder"}}
        
        if progress_callback:
            progress_callback(3, 3, "{operation_description} complete!")
        
        return result
        
    except Exception as e:
        if log_callback:
            log_callback(f"Error in {operation_description}: {{e}}")
        raise
""",
    
    "worker_usage": """
        # Use ThreadManager instead of QThread
        worker_id = start_worker(
            '{task_type}',
            {backend_function},
            {args},
            progress_callback=self.update_progress,
            log_callback=self.handle_error
        )
        
        # Store worker ID for potential cancellation
        self.current_worker_id = worker_id
        
        # Connect to ThreadManager signals for result handling
        thread_manager = get_thread_manager()
        thread_manager.worker_finished.connect(self._on_worker_finished)
        thread_manager.worker_error.connect(self._on_worker_error)
""",
    
    "signal_handlers": """
    def _on_worker_finished(self, worker_id: str):
        \"\"\"Handle worker completion.\"\"\"
        if hasattr(self, 'current_worker_id') and self.current_worker_id == worker_id:
            self.current_worker_id = None
            # The actual result handling will be done in the specific handler methods
    
    def _on_worker_error(self, worker_id: str, error_msg: str):
        \"\"\"Handle worker error.\"\"\"
        if hasattr(self, 'current_worker_id') and self.current_worker_id == worker_id:
            self.current_worker_id = None
            self.handle_error(error_msg)
"""
}

def backup_files():
    """Create backup of all UI files before migration."""
    if os.path.exists(BACKUP_DIR):
        shutil.rmtree(BACKUP_DIR)
    os.makedirs(BACKUP_DIR)
    
    for file_path in Path(UI_DIR).glob("*.py"):
        backup_path = os.path.join(BACKUP_DIR, file_path.name)
        shutil.copy2(file_path, backup_path)
    
    print(f"Backup created in {BACKUP_DIR}")

def find_qthread_usage(file_path):
    """Find QThread usage patterns in a file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    patterns = {
        'qthread_class': re.compile(r'class\s+(\w+)\s*\(\s*QThread\s*\)\s*:'),
        'worker_instantiation': re.compile(r'self\.worker\s*=\s*(\w+)\s*\('),
        'worker_start': re.compile(r'self\.worker\.start\s*\('),
        'signal_connection': re.compile(r'self\.worker\.(\w+)\.connect\s*\('),
    }
    
    results = {}
    for pattern_name, pattern in patterns.items():
        matches = pattern.findall(content)
        results[pattern_name] = matches
    
    return results

def migrate_file(file_path):
    """Migrate a single file to use ThreadManager."""
    print(f"Migrating {file_path}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add import for ThreadManager
    if 'from .worker_threads import start_worker, get_thread_manager' not in content:
        import_pattern = re.compile(r'(from PyQt6\.QtCore import.*?)(\n)')
        match = import_pattern.search(content)
        if match:
            new_import = match.group(1) + ', QThread' + match.group(2)
            new_import += 'from .worker_threads import start_worker, get_thread_manager\n'
            content = content.replace(match.group(0), new_import)
    
    # Remove QThread class definitions (they should already be commented out)
    # This is handled by the previous automation script
    
    # Add backend functions template
    if 'def ' in content and 'backend' not in content:
        # Find a good place to insert backend functions
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.strip().startswith('logger = logging.getLogger'):
                # Insert backend functions after logger setup
                backend_template = MIGRATION_TEMPLATES["analysis"].format(
                    operation_name="operation",
                    params="param1, param2",
                    operation_description="operation"
                )
                lines.insert(i + 1, backend_template)
                break
        content = '\n'.join(lines)
    
    # Replace worker usage patterns
    content = re.sub(
        r'self\.worker\s*=\s*(\w+)\s*\([^)]*\)\s*\n\s*self\.worker\.start\s*\(',
        lambda m: MIGRATION_TEMPLATES["worker_usage"].format(
            task_type="task",
            backend_function="backend_function",
            args="arg1, arg2"
        ),
        content
    )
    
    # Add signal handlers if not present
    if '_on_worker_finished' not in content:
        # Find a good place to insert signal handlers
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.strip().startswith('def handle_error'):
                # Insert signal handlers before handle_error
                signal_handlers = MIGRATION_TEMPLATES["signal_handlers"]
                lines.insert(i, signal_handlers)
                break
        content = '\n'.join(lines)
    
    # Write the migrated content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✓ Migrated {file_path}")

def main():
    """Main migration function."""
    print("=== AI Coder Assistant QThread Migration ===")
    print("This script will migrate all QThread subclasses to use ThreadManager")
    
    # Create backup
    print("\n1. Creating backup...")
    backup_files()
    
    # Find all Python files in UI directory
    ui_files = list(Path(UI_DIR).glob("*.py"))
    
    print(f"\n2. Found {len(ui_files)} UI files to process")
    
    # Migrate each file
    migrated_count = 0
    for file_path in ui_files:
        try:
            migrate_file(file_path)
            migrated_count += 1
        except Exception as e:
            print(f"✗ Error migrating {file_path}: {e}")
    
    print(f"\n3. Migration complete!")
    print(f"   - Migrated {migrated_count} files")
    print(f"   - Backup available in {BACKUP_DIR}")
    print(f"\n4. Next steps:")
    print(f"   - Review the migrated files")
    print(f"   - Implement actual backend logic in the placeholder functions")
    print(f"   - Test the application thoroughly")
    print(f"   - Remove the backup directory when satisfied")

if __name__ == "__main__":
    main() 