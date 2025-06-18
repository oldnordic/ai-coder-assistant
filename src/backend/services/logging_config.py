"""
logging_config.py

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

# src/core/logging_config.py
import logging
import os
from ..utils import settings

def setup_logging():
    """
    Sets up a centralized logging configuration for the application.
    """
    # Define the path for the log file within the new logs directory
    log_dir = os.path.join(settings.PROJECT_ROOT, "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_filepath = os.path.join(log_dir, "application.log")

    # Get the root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO) # Set the lowest level to capture all messages

    # Clear existing handlers to avoid duplicate logs from previous runs
    if logger.hasHandlers():
        logger.handlers.clear()

    # Create file handler which logs even debug messages
    # Use 'a' for append mode to keep logs between sessions
    file_handler = logging.FileHandler(log_filepath, mode='a', encoding='utf-8')
    file_handler.setLevel(logging.INFO)

    # Create console handler with a higher log level
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logging.info("Logging configured successfully. Log file at: %s", log_filepath)