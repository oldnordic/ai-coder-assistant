import os
import re

UI_DIR = "src/frontend/ui"
CHECKLIST_FILE = "QThread_Migration_Checklist.md"

QTHREAD_PATTERN = re.compile(r"class\s+(\w+)\s*\(\s*QThread\s*\)\s*:")

MIGRATION_TEMPLATE = '''
# MIGRATION NEEDED: Replace QThread subclass with ThreadManager pattern

# 1. Remove this QThread subclass.
# 2. Create a backend function for the threaded operation:
#    def backend_func(..., progress_callback=None, log_message_callback=None, cancellation_callback=None):
#        # do work, call callbacks, return result
# 3. In the UI, use:
#    from .worker_threads import start_worker
#    worker_id = start_worker("task_type", backend_func, ..., progress_callback=..., log_message_callback=...)
# 4. Connect ThreadManager signals to UI slots for progress, result, and error.
'''

def find_qthread_subclasses():
    qthread_classes = []
    for root, dirs, files in os.walk(UI_DIR):
        for fname in files:
            if fname.endswith(".py"):
                fpath = os.path.join(root, fname)
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()
                for match in QTHREAD_PATTERN.finditer(content):
                    class_name = match.group(1)
                    qthread_classes.append((fpath, class_name))
    return qthread_classes

def generate_checklist(qthread_classes):
    with open(CHECKLIST_FILE, "w", encoding="utf-8") as f:
        f.write("# QThread Migration Checklist\n\n")
        for fpath, class_name in qthread_classes:
            f.write(f"- [ ] `{class_name}` in `{fpath}`\n")
        f.write("\nSee MIGRATION_TEMPLATE in automate_qthread_migration.py for steps.\n")

def insert_migration_template(fpath, class_name):
    with open(fpath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    new_lines = []
    inside_class = False
    for line in lines:
        if re.match(rf"class\s+{class_name}\s*\(\s*QThread\s*\)\s*:", line):
            new_lines.append('"""\n' + MIGRATION_TEMPLATE + '\n"""\n')
            inside_class = True
            # Optionally, comment out the class definition
            new_lines.append("# " + line)
        elif inside_class and (line.strip() == "" or line.startswith("class ")):
            inside_class = False
            new_lines.append(line)
        elif inside_class:
            new_lines.append("# " + line)
        else:
            new_lines.append(line)
    with open(fpath, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

def main():
    qthread_classes = find_qthread_subclasses()
    if not qthread_classes:
        print("No QThread subclasses found.")
        return
    print(f"Found {len(qthread_classes)} QThread subclasses.")
    generate_checklist(qthread_classes)
    print(f"Checklist written to {CHECKLIST_FILE}")
    # Auto-insert migration templates and comment out QThread classes
    for fpath, class_name in qthread_classes:
        insert_migration_template(fpath, class_name)
    print("Migration templates inserted and QThread classes commented out.")

if __name__ == "__main__":
    main() 