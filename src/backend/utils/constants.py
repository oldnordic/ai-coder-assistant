"""
constants.py

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
Constants for the AI Coder Assistant application.
Centralizes magic numbers and configuration values.
"""

import os

# UI Layout Constants
WINDOW_DEFAULT_X = 100
WINDOW_DEFAULT_Y = 100
WINDOW_DEFAULT_WIDTH = 1200
WINDOW_DEFAULT_HEIGHT = 800

DIALOG_DEFAULT_X = 150
DIALOG_DEFAULT_Y = 150
DIALOG_DEFAULT_WIDTH = 900
DIALOG_DEFAULT_HEIGHT = 800

# Widget Heights
INPUT_HEIGHT = 100
LOG_CONSOLE_MAX_HEIGHT = 150
STATUS_BOX_MIN_HEIGHT = 200
CONTEXT_TEXT_MAX_HEIGHT = 100

# Progress Dialog Constants
PROGRESS_MIN = 0
PROGRESS_MAX = 100
PROGRESS_COMPLETE = 100

# Timeout Constants (seconds)
OLLAMA_TIMEOUT = 120
HTTP_TIMEOUT_SHORT = 5
HTTP_TIMEOUT_LONG = 30
WORKER_WAIT_TIME = 2000  # milliseconds
GRACEFUL_SHUTDOWN_WAIT = 3000  # milliseconds

# HTTP Status Codes
HTTP_OK = 200

# File Size Limits
MAX_FILE_SIZE = 1024 * 1024  # 1MB
MAX_CHAR_LENGTH = 2000
MAX_ERROR_MESSAGE_LENGTH = 100
MAX_SUGGESTION_LENGTH = 300
MAX_CODE_CONTEXT_LENGTH = 200
MAX_FILENAME_LENGTH = 100

# Content Limits
MAX_CONTENT_SIZE = 51200  # 50KB
CACHE_EXPIRY_DAYS = 7
CACHE_EXPIRY_SECONDS = CACHE_EXPIRY_DAYS * 24 * 3600

# UI Styling
DEFAULT_FONT_WEIGHT = 500
DEFAULT_TEXT_COLOR = "495057"
DEFAULT_BACKGROUND_COLOR = "#1F1F1F"
DEFAULT_FOREGROUND_COLOR = "#CCCCCC"
DEFAULT_BORDER_COLOR = "#444444"

# User Agent
DEFAULT_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

# API Endpoints
OLLAMA_API_BASE_URL = "http://localhost:11434/api"
OLLAMA_TAGS_ENDPOINT = f"{OLLAMA_API_BASE_URL}/tags"

# Percentage Calculations
PERCENTAGE_MULTIPLIER = 100
PROGRESS_WEIGHT_DOWNLOAD = 0.8

# UI Constants
WAIT_TIMEOUT_MS = 2000
WAIT_TIMEOUT_SHORT_MS = 1000
WAIT_TIMEOUT_LONG_MS = 3000
GRACEFUL_SHUTDOWN_WAIT_MS = 3000

# UI Layout Constants
SPLITTER_LEFT_SIZE = 400
SPLITTER_RIGHT_SIZE = 600

# Progress Constants
PROGRESS_WEIGHT_DOWNLOAD = 0.8

# Content Size Limits
MAX_DESCRIPTION_LENGTH = 150
MAX_CODE_SNIPPET_LENGTH = 200
MAX_PROMPT_LENGTH = 100

# File Size Limits
MAX_FILE_SIZE_KB = 512  # 512KB limit for better performance

# HTTP Constants
HTTP_TIMEOUT_SHORT = 5
HTTP_TIMEOUT_LONG = 30

# Default Values
DEFAULT_SEVERITY_COLOR = '888888'
DEFAULT_PERCENTAGE_MULTIPLIER = 100

# --- Added for continuous learning and backend modules ---
DEFAULT_TIMEOUT_MS = 2000  # 2 seconds
MAX_FILE_SIZE_BYTES = 1024 * 1024  # 1MB
DEFAULT_BATCH_SIZE = 64

# Cloud Models Constants
DEFAULT_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds
SUPPORTED_PROVIDERS = ["openai", "anthropic", "google", "azure", "aws_bedrock", "cohere"]

# Temporary directory for processing
TMP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "tmp")

# Data directory
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")

# Continuous Learning
CONTINUOUS_LEARNING_DB_PATH = os.path.join(DATA_DIR, "continuous_learning.db")
CONTINUOUS_LEARNING_MIN_INPUT_LENGTH = 10
CONTINUOUS_LEARNING_MIN_OUTPUT_LENGTH = 5
CONTINUOUS_LEARNING_MAX_INPUT_LENGTH = 10000
CONTINUOUS_LEARNING_MAX_OUTPUT_LENGTH = 5000
CONTINUOUS_LEARNING_REPLAY_BUFFER_SIZE = 1000
CONTINUOUS_LEARNING_QUALITY_THRESHOLD = 0.7
CONTINUOUS_LEARNING_BATCH_SIZE = 100
CONTINUOUS_LEARNING_UPDATE_INTERVAL_HOURS = 24 