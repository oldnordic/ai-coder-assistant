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
                # Read only the first 4000 characters to avoid overwhelming the context
                content = f.read(4000)
            return content
        else:
            return f"Error: File not found at '{filepath}'"
    except Exception as e:
        return f"An error occurred while trying to read the file: {e}"

def write_file_tool(filepath, content, project_root):
    """
    A tool that allows the AI to write or overwrite a file within the project.
    Includes security checks to prevent writing outside the project root.
    """
    try:
        # Security: Sanitize the filepath
        safe_path = os.path.abspath(os.path.join(project_root, filepath))
        if not safe_path.startswith(os.path.abspath(project_root)):
            return f"Error: Access denied. Cannot write files outside of the project directory."

        with open(safe_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Success: Wrote {len(content)} characters to {filepath}."
    except Exception as e:
        return f"An error occurred while trying to write the file: {e}"


# A dictionary that maps tool names to their functions
AVAILABLE_TOOLS = {
    "read_file": read_file_tool,
    "write_file": write_file_tool,
}