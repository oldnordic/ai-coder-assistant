#!/usr/bin/env python3
"""
Script to add GPL-3 license headers to Python files

This script adds the GPL-3 license header to all Python files in the project
that don't already have it.

Usage: python scripts/add_gpl_headers.py
"""

import os
import re
from pathlib import Path

# GPL-3 header template
GPL_HEADER = '''"""
{filename}

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

Copyright (C) 2024 AI Coder Assistant Contributors
"""

'''

def has_gpl_header(content):
    """Check if the file already has a GPL header."""
    return "GNU General Public License" in content and "Copyright (C)" in content

def add_gpl_header(file_path):
    """Add GPL header to a Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if has_gpl_header(content):
            print(f"Skipping {file_path} - already has GPL header")
            return False
        
        # Get the filename for the header
        filename = os.path.basename(file_path)
        
        # Create the header with the filename
        header = GPL_HEADER.format(filename=filename)
        
        # Add the header to the content
        new_content = header + content
        
        # Write back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"Added GPL header to {file_path}")
        return True
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Main function to process all Python files."""
    # Get the project root
    project_root = Path(__file__).parent.parent
    
    # Directories to process
    directories = [
        project_root / "src",
        project_root / "api",
        project_root / "scripts",
    ]
    
    # Files to skip
    skip_files = {
        "main.py",  # Already processed
        "__init__.py",  # Usually just imports
        "add_gpl_headers.py",  # This script
    }
    
    total_files = 0
    processed_files = 0
    
    for directory in directories:
        if not directory.exists():
            continue
            
        for file_path in directory.rglob("*.py"):
            if file_path.name in skip_files:
                continue
                
            total_files += 1
            if add_gpl_header(file_path):
                processed_files += 1
    
    print(f"\nSummary:")
    print(f"Total Python files found: {total_files}")
    print(f"Files processed: {processed_files}")
    print(f"Files skipped (already had headers): {total_files - processed_files}")

if __name__ == "__main__":
    main() 