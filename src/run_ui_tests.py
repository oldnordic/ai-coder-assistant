#!/usr/bin/env python3
"""
run_ui_tests.py - UI Test Runner for AI Coder Assistant

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

import os
import sys
import subprocess
import time
import signal
from pathlib import Path

def setup_environment():
    """Set up the environment for UI testing."""
    # Set headless Qt environment
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    os.environ['DISPLAY'] = ':99'
    
    # Set test environment variables
    os.environ['PYTEST_QT_API'] = 'pyqt6'
    os.environ['PYTEST_QT_TIMEOUT'] = '5000'
    
    # Add src to Python path
    src_path = Path(__file__).parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

def run_tests_with_timeout(test_path: str, timeout: int = 30) -> bool:
    """
    Run tests with a timeout to prevent hanging.
    
    Args:
        test_path: Path to test file or directory
        timeout: Timeout in seconds
        
    Returns:
        True if tests passed, False otherwise
    """
    try:
        # Run pytest with specific options for UI testing
        cmd = [
            sys.executable, '-m', 'pytest',
            test_path,
            '--tb=short',
            '--timeout=' + str(timeout),
            '--timeout-method=thread',
            '--disable-warnings',
            '-v'
        ]
        
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, timeout=timeout, capture_output=True, text=True)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print(f"Tests timed out after {timeout} seconds")
        return False
    except Exception as e:
        print(f"Error running tests: {e}")
        return False

def run_safe_ui_tests():
    """Run UI tests with proper error handling and cleanup."""
    setup_environment()
    
    # Test files to run (in order of priority)
    test_files = [
        'tests/frontend_backend/test_ai_tab_widgets.py',
        'tests/frontend_backend/test_main_window.py',
        'tests/frontend_backend/test_collaboration_tab.py',
        'tests/frontend_backend/test_code_standards_tab.py',
        'tests/frontend_backend/test_security_intelligence_tab.py',
        'tests/frontend_backend/test_pr_management_tab.py',
        'tests/frontend_backend/test_continuous_learning_tab.py',
        'tests/frontend_backend/test_refactoring_tab.py',
        'tests/frontend_backend/test_cloud_models_tab.py',
        'tests/frontend_backend/test_advanced_analytics_tab.py',
        'tests/frontend_backend/test_suggestion_dialog.py',
        'tests/frontend_backend/test_thread_monitor.py',
        'tests/frontend_backend/test_worker_threads_backend.py'
    ]
    
    results = {}
    total_passed = 0
    total_failed = 0
    
    print("=" * 60)
    print("UI TEST RUNNER - AI Coder Assistant")
    print("=" * 60)
    
    for test_file in test_files:
        if not os.path.exists(test_file):
            print(f"⚠️  Test file not found: {test_file}")
            continue
            
        print(f"\n🧪 Running: {test_file}")
        print("-" * 40)
        
        start_time = time.time()
        success = run_tests_with_timeout(test_file, timeout=15)
        end_time = time.time()
        
        duration = end_time - start_time
        results[test_file] = {
            'success': success,
            'duration': duration
        }
        
        if success:
            print(f"✅ PASSED ({duration:.2f}s)")
            total_passed += 1
        else:
            print(f"❌ FAILED ({duration:.2f}s)")
            total_failed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {len(results)}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")
    print(f"Success Rate: {(total_passed / len(results) * 100):.1f}%" if results else "0%")
    
    # Detailed results
    print("\nDetailed Results:")
    for test_file, result in results.items():
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"  {status} {test_file} ({result['duration']:.2f}s)")
    
    return total_failed == 0

if __name__ == '__main__':
    success = run_safe_ui_tests()
    sys.exit(0 if success else 1) 