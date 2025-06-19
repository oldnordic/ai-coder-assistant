#!/usr/bin/env python3
"""
Test runner for AI Coder Assistant

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

import unittest
import sys
import os
import time
import traceback
import subprocess

def run_all_tests():
    """Run all unit tests and return results."""
    print("=== AI Coder Assistant Test Suite ===")
    print("Running comprehensive unit tests...")
    print()
    
    # Add src to path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
    
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = 'tests'
    
    if not os.path.exists(start_dir):
        print(f"Error: Test directory '{start_dir}' not found")
        return False
    
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    start_time = time.time()
    
    try:
        result = runner.run(suite)
        end_time = time.time()
        
        print()
        print("=== Test Results Summary ===")
        print(f"Tests run: {result.testsRun}")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
        print(f"Time taken: {end_time - start_time:.2f} seconds")
        
        if result.failures:
            print("\n=== Failures ===")
            for test, traceback_str in result.failures:
                print(f"FAIL: {test}")
                print(traceback_str)
                print()
        
        if result.errors:
            print("\n=== Errors ===")
            for test, traceback_str in result.errors:
                print(f"ERROR: {test}")
                print(traceback_str)
                print()
        
        success = result.wasSuccessful()
        if success:
            print("✅ All tests passed!")
        else:
            print("❌ Some tests failed!")
        
        return success
        
    except Exception as e:
        print(f"Error running tests: {e}")
        traceback.print_exc()
        return False

def run_specific_test(test_name):
    """Run a specific test module."""
    print(f"=== Running Test: {test_name} ===")
    
    # Add src to path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
    
    try:
        # Import and run specific test
        test_module = __import__(f'tests.{test_name}', fromlist=['*'])
        
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(test_module)
        
        runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
        result = runner.run(suite)
        
        return result.wasSuccessful()
        
    except ImportError as e:
        print(f"Error importing test module {test_name}: {e}")
        return False
    except Exception as e:
        print(f"Error running test {test_name}: {e}")
        traceback.print_exc()
        return False

def main():
    """Main test runner function."""
    if len(sys.argv) > 1:
        # Run specific test
        test_name = sys.argv[1]
        success = run_specific_test(test_name)
    else:
        # Run all tests
        success = run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
    print("\n=== Running direct main.py import test (should not fail) ===")
    result = subprocess.run([sys.executable, 'main.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        print("main.py failed to run directly!\nSTDOUT:\n", result.stdout.decode(), "\nSTDERR:\n", result.stderr.decode())
        sys.exit(1)
    else:
        print("main.py ran successfully as a script.") 