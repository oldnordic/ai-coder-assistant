#!/usr/bin/env python3
"""Test runner for core modules."""

import os
import sys
from pathlib import Path

import pytest


def run_tests():
    """Run core module tests."""
    # Get the directory containing this script
    test_dir = Path(__file__).parent

    # Add the src directory to Python path
    src_dir = test_dir.parent.parent
    sys.path.insert(0, str(src_dir))

    # Run tests with coverage
    pytest_args = [
        "--verbose",
        "--cov=src.core",
        "--cov-report=term-missing",
        "--cov-report=html:coverage_report",
        os.path.join(test_dir, "core"),
    ]

    return pytest.main(pytest_args)


if __name__ == "__main__":
    sys.exit(run_tests())
