#!/usr/bin/env python3
import subprocess
import sys
import re
from typing import Dict, List, Tuple

def run_tests(test_path: str = None) -> Tuple[int, str]:
    """Run pytest and return the exit code and output."""
    cmd = ["python", "-m", "pytest", "-v"]
    if test_path:
        cmd.append(test_path)
    
    process = subprocess.run(cmd, capture_output=True, text=True)
    return process.returncode, process.stdout + process.stderr

def parse_test_results(output: str) -> Dict[str, List[str]]:
    """Parse the pytest output and return a dictionary of passed and failed tests."""
    results = {
        "passed": [],
        "failed": [],
        "errors": [],
        "warnings": []
    }
    
    # Extract test names and results
    test_pattern = r"(test_[^\s]+)\s+(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS)"
    for match in re.finditer(test_pattern, output):
        test_name, result = match.groups()
        if result == "PASSED":
            results["passed"].append(test_name)
        elif result == "FAILED":
            results["failed"].append(test_name)
        elif result == "ERROR":
            results["errors"].append(test_name)
    
    # Extract warnings
    warning_pattern = r"Warning:\s+(.+?)(?=\n|$)"
    for match in re.finditer(warning_pattern, output):
        results["warnings"].append(match.group(1))
    
    return results

def print_summary(results: Dict[str, List[str]], exit_code: int, output: str) -> None:
    """Print a summary of the test results."""
    print("\n=== Test Summary ===")
    print(f"Total tests: {len(results['passed']) + len(results['failed']) + len(results['errors'])}")
    print(f"Passed: {len(results['passed'])}")
    print(f"Failed: {len(results['failed'])}")
    print(f"Errors: {len(results['errors'])}")
    print(f"Warnings: {len(results['warnings'])}")
    print(f"Exit code: {exit_code}")
    
    if results["failed"]:
        print("\nFailed tests:")
        for test in results["failed"]:
            print(f"  - {test}")
    
    if results["errors"]:
        print("\nTests with errors:")
        for test in results["errors"]:
            print(f"  - {test}")
    
    if results["warnings"]:
        print("\nWarnings:")
        for warning in results["warnings"]:
            print(f"  - {warning}")
    
    # If there are failures or errors, print the full output for debugging
    if results["failed"] or results["errors"]:
        print("\nFull test output:")
        print(output)

def main() -> int:
    """Main function that runs tests and prints results."""
    test_path = sys.argv[1] if len(sys.argv) > 1 else None
    exit_code, output = run_tests(test_path)
    results = parse_test_results(output)
    print_summary(results, exit_code, output)
    return exit_code

if __name__ == "__main__":
    sys.exit(main()) 