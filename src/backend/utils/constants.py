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

from .config import get_url, get_timeout, get_limit, get_ui_setting, get_scan_setting

# UI Layout Constants
import os
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

# Window and Dialog Sizes
MAIN_WINDOW_MIN_WIDTH = get_ui_setting("main_window_min_width")
MAIN_WINDOW_MIN_HEIGHT = get_ui_setting("main_window_min_height")
LOG_OUTPUT_MAX_HEIGHT = get_ui_setting("log_output_max_height")
DOC_URLS_INPUT_MAX_HEIGHT = get_ui_setting("doc_urls_input_max_height")

# Progress Dialog Constants
PROGRESS_MIN = 0
PROGRESS_MAX = 100
PROGRESS_COMPLETE = 100
PROGRESS_DIALOG_MAX_VALUE = get_ui_setting("progress_dialog_max_value")
PROGRESS_DIALOG_MIN_VALUE = get_ui_setting("progress_dialog_min_value")
PROGRESS_WEIGHT_DOWNLOAD = 0.8

# Timer and Processing Constants
LOG_QUEUE_PROCESS_INTERVAL_MS = 100

# Web Scraping Defaults
DEFAULT_MAX_PAGES = 100
DEFAULT_MAX_DEPTH = 5
DEFAULT_LINKS_PER_PAGE = 20
DEFAULT_MAX_PAGES_SPINBOX_VALUE = get_limit("max_pages_spinbox_value")
DEFAULT_MAX_DEPTH_SPINBOX_VALUE = get_limit("max_depth_spinbox_value")
DEFAULT_LINKS_PER_PAGE_SPINBOX_VALUE = 50
MAX_PAGES_SPINBOX_RANGE = (1, 100)
MAX_DEPTH_SPINBOX_RANGE = (1, 10)
MAX_LINKS_PER_PAGE_SPINBOX_RANGE = 100

# Timeout Constants (seconds)
OLLAMA_TIMEOUT = 120
WORKER_WAIT_TIME = 2000  # milliseconds
GRACEFUL_SHUTDOWN_WAIT = 3000  # milliseconds

# HTTP Status Codes
HTTP_OK = 200
HTTP_TIMEOUT_SHORT = get_timeout("http_short")
HTTP_TIMEOUT_LONG = get_timeout("http_long")
HTTP_CREATED = 201
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_INTERNAL_SERVER_ERROR = 500

# File Size Limits
MAX_FILE_SIZE = 1024 * 1024  # 1MB
MAX_CHAR_LENGTH = 2000
MAX_ERROR_MESSAGE_LENGTH = get_limit("max_error_message_length")
MAX_SUGGESTION_LENGTH = get_limit("max_suggestion_length")
MAX_CODE_CONTEXT_LENGTH = get_limit("max_code_context_length")
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
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# API Endpoints
OLLAMA_API_BASE_URL = get_url("ollama_api")
OLLAMA_TAGS_ENDPOINT = f"{OLLAMA_API_BASE_URL}/tags"
OLLAMA_BASE_URL = get_url("ollama_base")
LM_STUDIO_BASE_URL = get_url("lm_studio_base")
WEB_SERVER_DEFAULT_HOST = get_url("web_server_default_host")
WEB_SERVER_DEFAULT_PORT = get_url("web_server_default_port")
API_SERVER_DEFAULT_PORT = get_url("api_server_default_port")

# Percentage Calculations
PERCENTAGE_MULTIPLIER = 100

# UI Constants
WAIT_TIMEOUT_MS = 2000
WAIT_TIMEOUT_SHORT_MS = 1000
WAIT_TIMEOUT_LONG_MS = 3000
GRACEFUL_SHUTDOWN_WAIT_MS = 3000

# UI Layout Constants
SPLITTER_LEFT_SIZE = 400
SPLITTER_RIGHT_SIZE = 600

# UI Table Headers and Labels
SCAN_RESULTS_TABLE_HEADERS = ["File", "Line", "Type", "Severity", "Issue", "Actions"]
MODEL_SOURCE_OPTIONS = ["Ollama", "Fine-tuned Local Model"]
DEFAULT_INCLUDE_PATTERNS = "*.py,*.js,*.ts,*.java,*.cpp,*.c,*.h,*.hpp"
DEFAULT_EXCLUDE_PATTERNS = "__pycache__/*,node_modules/*,.git/*,*.pyc,*.log"

# UI Status Messages
STATUS_READY_TO_SCAN = "Ready to scan"
STATUS_NO_ISSUES_FOUND = "No issues found"
STATUS_ENHANCEMENT_COMPLETE = "Enhancement complete."
STATUS_MODEL_NOT_LOADED = "Status: Not Loaded"
STATUS_NO_MODEL_INFO = "No model information available"

# UI Button Labels
BUTTON_BROWSE = "Browse..."
BUTTON_RUN_QUICK_SCAN = "Run Quick Scan"
BUTTON_STOP_SCAN = "Stop Scan"
BUTTON_REFRESH_MODELS = "Refresh Models"
BUTTON_LOAD_MODEL = "Load Fine-tuned Model"
BUTTON_ENHANCE_ALL = "Enhance All Issues with AI"
BUTTON_EXPORT_RESULTS = "Export Results"
BUTTON_AI_ENHANCE = "AI Enhance"

# UI Group Box Titles
GROUP_MODEL_CONFIG = "1. AI Model Configuration"
GROUP_SCAN_CONFIG = "2. Quick Scan Configuration"
GROUP_SCAN_RESULTS = "3. Scan Results & AI Enhancement"

# UI Form Labels
LABEL_MODEL_SOURCE = "Model Source:"
LABEL_OLLAMA_MODEL = "Ollama Model:"
LABEL_MODEL_STATUS = "Model Status:"
LABEL_MODEL_INFO = "Model Info:"
LABEL_PROJECT_DIRECTORY = "Project Directory:"
LABEL_INCLUDE_PATTERNS = "Include Patterns:"
LABEL_EXCLUDE_PATTERNS = "Exclude Patterns:"

# UI Placeholder Texts
PLACEHOLDER_PROJECT_DIR = "Select a project folder to scan..."

# UI Error Messages
ERROR_DOCKER_TIMEOUT = "Docker operation timed out."
ERROR_AI_PARSING_FAILED = "Failed to parse AI response."
ERROR_NO_MODEL_AVAILABLE = "No AI model available"

# UI Success Messages
SUCCESS_SECRET_SAVED = "Secret saved successfully"
SUCCESS_MODEL_SWITCHED = "Switched to model:"

# UI Warning Messages
WARNING_NO_DOTENV = "python-dotenv not available. .env files will not be loaded."
WARNING_NO_ENV_FILE = "No .env file found at"
WARNING_UNKNOWN_PROVIDER = "Unknown provider:"
WARNING_MODEL_NOT_AVAILABLE = "Model not available"
WARNING_NO_OLLAMA_MODELS = "No Ollama models found. AI enhancement will be disabled."

# Progress Constants

# Content Size Limits
MAX_DESCRIPTION_LENGTH = get_limit("max_description_length")
MAX_CODE_SNIPPET_LENGTH = get_limit("max_code_snippet_length")
MAX_PROMPT_LENGTH = get_limit("max_prompt_length")

# File Size Limits
MAX_FILE_SIZE_KB = get_limit("max_file_size_kb")

# Default Values
DEFAULT_SEVERITY_COLOR = "888888"
DEFAULT_PERCENTAGE_MULTIPLIER = 100

# --- Added for continuous learning and backend modules ---
DEFAULT_TIMEOUT_MS = 2000  # 2 seconds
MAX_FILE_SIZE_BYTES = 1024 * 1024  # 1MB
DEFAULT_BATCH_SIZE = 64

# Cloud Models Constants
DEFAULT_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds
SUPPORTED_PROVIDERS = [
    "openai",
    "anthropic",
    "google",
    "azure",
    "aws_bedrock",
    "cohere",
]

# Scanner Constants
MAX_ISSUES_PER_FILE = get_limit("max_issues_per_file")
SCAN_TIMEOUT_SECONDS = get_timeout("scan")
BYTES_PER_KB = get_scan_setting("bytes_per_kb")
DEFAULT_SCAN_LIMIT = get_scan_setting("default_scan_limit")
AI_SUGGESTION_TIMEOUT_SECONDS = get_timeout("ai_suggestion")
LINTER_TIMEOUT_SECONDS = get_timeout("linter")

# Test Constants
TEST_TIMEOUT_MS = 5000
TEST_WAIT_TIMEOUT_MS = 1000
TEST_WAIT_LONG_TIMEOUT_MS = 3000
TEST_ITERATION_COUNT = 100
TEST_LARGE_ITERATION_COUNT = 1000
TEST_MEDIUM_ITERATION_COUNT = 500
TEST_SMALL_ITERATION_COUNT = 200
TEST_TASK_ID_123 = "123"
TEST_TASK_ID_456 = "456"
TEST_TASK_ID_789 = "789"
TEST_INVALID_TASK_ID = 99999
TEST_TEMPERATURE = 0.7
TEST_MAX_TOKENS = 1000
TEST_CONTEXT_LENGTH = 8192
TEST_FILE_SIZE = 1024
TEST_SCAN_DURATION = 300
TEST_BATCH_SIZE = 100
TEST_CLEANUP_DAYS = 30
TEST_USER_RATING = 3
TEST_PORT = 8080
TEST_DELAY_MS = 5

# Logging Constants
LOG_ROTATION_MAX_BYTES = 10 * 1024 * 1024  # 10MB

# Temporary directory for processing
TMP_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "tmp"
)

# Data directory
DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data"
)

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

# Markdown Viewer Defaults
MARKDOWN_VIEWER_WIDTH = 800
MARKDOWN_VIEWER_HEIGHT = 600
MARKDOWN_VIEWER_FONT_SIZE = 14
MARKDOWN_VIEWER_FONT_FAMILY = "Consolas, 'Courier New', monospace"
MARKDOWN_VIEWER_BG_COLOR = "#1F1F1F"
MARKDOWN_VIEWER_FG_COLOR = "#CCCCCC"

DEFAULT_MAX_WORKERS = get_scan_setting("default_max_workers")

SSL_VERIFY_DEFAULT = True
VERIFY_DEFAULT = True

# Collaboration Constants
COLLABORATION_TAB_TITLE = "Collaboration Features"
COLLABORATION_DESCRIPTION = "Team collaboration tools for code sharing, communication, and project management."
CONFIGURE_PLATFORMS_BUTTON = "Configure Platforms"
TEAM_CHAT_TAB = "Team Chat"
CODE_SHARING_TAB = "Code Sharing"
PROJECT_MANAGEMENT_TAB = "Project Management"

# Collaboration Platform Names
PLATFORM_TEAMS = "Microsoft Teams"
PLATFORM_SLACK = "Slack"
PLATFORM_GITHUB = "GitHub"
PLATFORM_STATUS_ACTIVE = "Active Platforms: "
PLATFORM_STATUS_NONE = "None (Configure platforms to enable integration)"

# Code Sharing Constants
CODE_SHARING_TITLE = "Code Sharing & Collaboration"
SHARE_NEW_ITEM_GROUP = "Share New Item"
SHARE_TYPE_LABEL = "Share Type:"
SHARE_FILE_BUTTON = "Share File"
SHARE_SNIPPET_BUTTON = "Share Code Snippet"
SHARE_DOC_BUTTON = "Share Documentation"
SHARED_ITEMS_GROUP = "Shared Items"
FILTER_BY_LABEL = "Filter by:"

# Share Types
SHARE_TYPE_FILE = "File"
SHARE_TYPE_SNIPPET = "Code Snippet"
SHARE_TYPE_DOCUMENTATION = "Documentation"
SHARE_TYPE_CONFIGURATION = "Configuration"

# Model Manager Constants
MODEL_MANAGER_TITLE = "Model Manager"
CURRENT_MODEL_STATUS_GROUP = "Current Model Status"
ACTIVE_MODEL_LABEL = "Active Model:"
SWITCH_TO_LABEL = "Switch to:"
SELECT_MODEL_PLACEHOLDER = "Select Model"

# Model Health Constants
HEALTH_OVERVIEW_GROUP = "Model Health Overview"
HEALTH_STATUS_LABEL = "Status:"
RESPONSE_TIME_LABEL = "Response Time:"
LAST_CHECK_LABEL = "Last Check:"
RUN_HEALTH_CHECK_BUTTON = "Run Health Check"
REFRESH_SYSTEM_INFO_BUTTON = "Refresh System Info"

# Health Status Colors
HEALTH_COLOR_GREEN = "#28a745"
HEALTH_COLOR_RED = "#dc3545"
HEALTH_COLOR_YELLOW = "#ffc107"
HEALTH_COLOR_BLUE = "#007bff"

# Health Status Messages
HEALTH_STATUS_HEALTHY = "Healthy"
HEALTH_STATUS_UNHEALTHY = "Unhealthy"
HEALTH_STATUS_NO_MODEL = "No Model"
HEALTH_STATUS_ERROR = "Error"
HEALTH_STATUS_CHECKING = "Checking..."

# Model Types
MODEL_TYPE_OLLAMA = "ollama"
MODEL_TYPE_FINE_TUNED = "fine_tuned"
MODEL_TYPE_LOCAL = "local"

# Model Actions
MODEL_ACTION_SET_ACTIVE = "Set Active"
MODEL_ACTION_DELETE = "Delete"
MODEL_ACTION_EVALUATE = "Evaluate"
MODEL_ACTION_REFRESH = "Refresh"

# Training Constants
TRAINING_START_BUTTON = "Start Training"
TRAINING_STOP_BUTTON = "Stop Training"
TRAINING_CREATE_DATASET_BUTTON = "Create Dataset"
TRAINING_BROWSE_DATASETS_BUTTON = "Browse Datasets"
