# main.py
"""
AI Coder Assistant - Main Application Entry Point

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

"""
This is the main entry point for the AI Coder Assistant application.
It delegates to the src.main module to follow Python best practices.

To run the application, use one of these methods:

1. From the project root:
   python -m src.main

2. Or simply:
   python main.py

Both methods will work, but the module approach (-m src.main) is preferred
as it follows Python best practices for package imports.
"""

def main():
    """Main entry point that delegates to the src.main module."""
    # Import and run the main function from src.main
    from src.main import main as src_main
    src_main()

if __name__ == '__main__':
    main()