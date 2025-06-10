import os

def read_file_tool(filepath, project_root):
    """
    A tool that allows the AI to read the content of a file within the project.
    To prevent security issues, it only allows reading files within the project root.
    """
    try:
        # Security: Sanitize the filepath to prevent directory traversal
        safe_path = os.path.abspath(os.path.join(project_root, filepath))
        if not safe_path.startswith(os.path.abspath(project_root)):
            return f"Error: Access denied. Cannot read files outside of the project directory."

        if os.path.exists(safe_path):
            with open(safe_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Read only the first 2000 characters to avoid overwhelming the context
                content = f.read(2000) 
            return content
        else:
            return f"Error: File not found at '{filepath}'"
    except Exception as e:
        return f"An error occurred while trying to read the file: {e}"

# A dictionary that maps tool names to their functions
AVAILABLE_TOOLS = {
    "read_file": read_file_tool
}