"""
conftest.py - Shared pytest fixtures for UI testing

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

import pytest
import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer, QThread
from unittest.mock import MagicMock, patch

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

@pytest.fixture(scope="session")
def app():
    """
    Create a single QApplication instance for the entire test session.
    This prevents crashes from multiple QApplication instances.
    """
    # Check if QApplication already exists
    app_instance = QApplication.instance()
    if app_instance is None:
        app_instance = QApplication(sys.argv)
    
    # Set up proper cleanup
    def cleanup():
        # Process any pending events
        app_instance.processEvents()
        # Clean up any remaining threads
        current_thread = QThread.currentThread()
        if current_thread:
            for thread in current_thread.findChildren(QThread):
                if thread != current_thread:
                    thread.quit()
                    thread.wait(1000)  # Wait up to 1 second
    
    # Register cleanup
    import atexit
    atexit.register(cleanup)
    
    yield app_instance
    
    # Final cleanup
    cleanup()

@pytest.fixture(autouse=True)
def cleanup_after_test():
    """
    Clean up after each test to prevent signal/slot issues.
    """
    yield
    
    # Process any pending events
    app = QApplication.instance()
    if app:
        app.processEvents()
    
    # Clear any remaining timers - FIXED: Use proper static method call
    try:
        # Get all QTimer instances from the application
        app = QApplication.instance()
        if app:
            for timer in app.findChildren(QTimer):
                timer.stop()
    except Exception:
        # Ignore timer cleanup errors
        pass

@pytest.fixture
def mock_backend_services():
    """
    Mock all backend services to prevent real network/database calls.
    """
    with patch('backend.services.task_management.get_task_management_service') as mock_task, \
         patch('backend.services.continuous_learning.get_continuous_learning_service') as mock_cl, \
         patch('backend.services.ollama_client.get_available_models_sync') as mock_ollama, \
         patch('backend.services.api.get_llm_manager') as mock_llm, \
         patch('backend.services.security_intelligence.SecurityIntelligenceService') as mock_security, \
         patch('backend.services.code_standards.CodeStandardsService') as mock_standards, \
         patch('backend.services.pr_automation.PRAutomationService') as mock_pr, \
         patch('backend.services.performance_optimization.PerformanceOptimizationService') as mock_perf, \
         patch('backend.services.web_server.WebServerService') as mock_web, \
         patch('backend.services.cloud_models.CloudModelsService') as mock_cloud, \
         patch('backend.services.advanced_analytics.AdvancedAnalyticsService') as mock_analytics:
        
        # Set up mock return values
        mock_task.return_value = MagicMock()
        mock_cl.return_value = MagicMock()
        mock_ollama.return_value = []
        mock_llm.return_value = MagicMock()
        mock_security.return_value = MagicMock()
        mock_standards.return_value = MagicMock()
        mock_pr.return_value = MagicMock()
        mock_perf.return_value = MagicMock()
        mock_web.return_value = MagicMock()
        mock_cloud.return_value = MagicMock()
        mock_analytics.return_value = MagicMock()
        
        yield {
            'task': mock_task,
            'continuous_learning': mock_cl,
            'ollama': mock_ollama,
            'llm': mock_llm,
            'security': mock_security,
            'standards': mock_standards,
            'pr': mock_pr,
            'performance': mock_perf,
            'web': mock_web,
            'cloud': mock_cloud,
            'analytics': mock_analytics
        }

@pytest.fixture
def safe_qtbot(qtbot):
    """
    A safer qtbot that handles cleanup properly.
    """
    yield qtbot
    
    # Process events after each test
    try:
        qtbot.wait(100)  # Small delay to let signals propagate
        qtbot.waitUntil(lambda: True, timeout=1000)  # Wait for any pending events
    except Exception:
        # Ignore qtbot errors
        pass 