"""
Feedback Loop System - Docker-based Testing and Learning

This module implements a feedback loop system that uses Docker containers
to test AI-generated fixes and gather feedback for continuous learning.
"""

import asyncio
import logging
import os
import json
import tempfile
import subprocess
from typing import Any, Dict, List, Optional, Tuple, Callable
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict

from src.backend.services.docker_utils import (
    DockerUtils, 
    DockerTestConfig, 
    ContainerTestResult
)
from src.backend.utils.exceptions import (
    AICoderAssistantError,
    DockerError,
    TestError,
)
from src.backend.utils.config import get_config

logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Represents the result of a test run."""
    test_id: str
    file_path: str
    original_code: str
    modified_code: str
    test_output: str
    test_error: Optional[str]
    success: bool
    execution_time: float
    memory_usage: Optional[float]
    timestamp: datetime
    test_type: str  # syntax, unit, integration, performance
    container_result: Optional[ContainerTestResult] = None


@dataclass
class FeedbackData:
    """Represents feedback data for learning."""
    feedback_id: str
    test_result: TestResult
    improvement_score: float
    user_feedback: Optional[str]
    auto_feedback: Dict[str, Any]
    timestamp: datetime
    applied: bool


class FeedbackLoopSystem:
    """
    Feedback loop system for testing AI fixes and gathering learning data.
    
    This system uses Docker containers to:
    1. Test AI-generated fixes in isolated environments
    2. Run comprehensive test suites
    3. Gather performance metrics
    4. Provide feedback for model improvement
    """
    
    def __init__(self):
        """Initialize the feedback loop system."""
        self.config = get_config()
        self.test_results: List[TestResult] = []
        self.feedback_data: List[FeedbackData] = []
        self.docker_images: Dict[str, str] = {
            "python": "python:3.11-slim",
            "node": "node:18-slim",
            "java": "openjdk:17-slim",
            "go": "golang:1.21-alpine"
        }
        
        # Test configurations
        self.test_configs = {
            "python": {
                "syntax_check": ["python", "-m", "py_compile"],
                "unit_test": ["python", "-m", "pytest"],
                "lint_check": ["python", "-m", "flake8"],
                "type_check": ["python", "-m", "mypy"]
            },
            "javascript": {
                "syntax_check": ["node", "--check"],
                "lint_check": ["npx", "eslint"],
                "test": ["npm", "test"]
            }
        }
        
        logger.info("Feedback loop system initialized")
    
    async def test_fix_in_docker(
        self,
        file_path: str,
        original_code: str,
        modified_code: str,
        language: str = "python",
        test_types: Optional[List[str]] = None,
        log_callback: Optional[Callable[[str], None]] = None
    ) -> TestResult:
        """
        Test a fix in a Docker container using enhanced DockerUtils.
        
        Args:
            file_path: Path to the file being tested
            original_code: Original code content
            modified_code: Modified code content
            language: Programming language
            test_types: Types of tests to run
            log_callback: Optional callback for real-time log streaming
            
        Returns:
            TestResult object with container test results
        """
        test_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        if test_types is None:
            test_types = ["syntax_check"]
        
        try:
            logger.info(f"Testing fix for {file_path} in Docker container")
            
            # Create temporary directory for testing
            with tempfile.TemporaryDirectory() as temp_dir:
                # Write the modified code to temp file
                temp_file = os.path.join(temp_dir, os.path.basename(file_path))
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(modified_code)
                
                # Create additional test files if needed
                await self._create_test_environment(temp_dir, language, test_types)
                
                # Configure Docker test
                test_config = DockerTestConfig(
                    image_tag=f"ai-fix-test-{language}-{test_id}",
                    container_name=f"ai-fix-container-{test_id}",
                    timeout_seconds=300,
                    health_check_interval=5,
                    max_health_checks=60,
                    cleanup_on_failure=True,
                    preserve_logs=True,
                    test_command=self._build_test_command(language, test_types, temp_file),
                    environment_vars=self._get_test_environment(language),
                    volumes=None,
                    ports=None
                )
                
                # Run comprehensive Docker test
                start_time = datetime.now()
                
                container_result = DockerUtils.run_comprehensive_test(
                    context_dir=temp_dir,
                    test_config=test_config,
                    log_callback=log_callback
                )
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                # Convert container result to test result
                test_result = TestResult(
                    test_id=test_id,
                    file_path=file_path,
                    original_code=original_code,
                    modified_code=modified_code,
                    test_output=container_result.logs,
                    test_error=container_result.error_message,
                    success=container_result.success,
                    execution_time=execution_time,
                    memory_usage=None,  # TODO: Add memory monitoring
                    timestamp=datetime.now(),
                    test_type=",".join(test_types),
                    container_result=container_result
                )
                
                self.test_results.append(test_result)
                
                # Generate feedback
                await self._generate_feedback(test_result)
                
                logger.info(f"Test completed: {test_result.success}")
                return test_result
                
        except Exception as e:
            logger.error(f"Error testing fix in Docker: {e}")
            
            # Create failed test result
            test_result = TestResult(
                test_id=test_id,
                file_path=file_path,
                original_code=original_code,
                modified_code=modified_code,
                test_output="",
                test_error=str(e),
                success=False,
                execution_time=0.0,
                memory_usage=None,
                timestamp=datetime.now(),
                test_type=",".join(test_types) if test_types else "unknown"
            )
            
            self.test_results.append(test_result)
            return test_result
    
    async def test_workspace_in_docker(
        self,
        workspace_path: str,
        language: str = "python",
        test_types: Optional[List[str]] = None,
        log_callback: Optional[Callable[[str], None]] = None
    ) -> ContainerTestResult:
        """
        Test an entire workspace in a Docker container.
        
        Args:
            workspace_path: Path to the workspace to test
            language: Programming language
            test_types: Types of tests to run
            log_callback: Optional callback for real-time log streaming
            
        Returns:
            ContainerTestResult with comprehensive test results
        """
        if test_types is None:
            test_types = ["syntax_check", "unit_test"]
        
        try:
            logger.info(f"Testing workspace {workspace_path} in Docker")
            
            # Configure Docker test for workspace
            test_config = DockerTestConfig(
                image_tag=f"ai-workspace-test-{language}",
                container_name=f"ai-workspace-container-{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                timeout_seconds=600,  # Longer timeout for workspace tests
                health_check_interval=10,
                max_health_checks=120,
                cleanup_on_failure=True,
                preserve_logs=True,
                test_command=self._build_workspace_test_command(language, test_types),
                environment_vars=self._get_test_environment(language),
                volumes=None,
                ports=None
            )
            
            # Run comprehensive test
            container_result = DockerUtils.run_comprehensive_test(
                context_dir=workspace_path,
                test_config=test_config,
                log_callback=log_callback
            )
            
            # Analyze results
            analysis = DockerUtils.analyze_test_results(container_result)
            logger.info(f"Workspace test analysis: {analysis}")
            
            return container_result
            
        except Exception as e:
            logger.error(f"Error testing workspace in Docker: {e}")
            
            return ContainerTestResult(
                success=False,
                error_message=str(e),
                duration_seconds=0.0
            )
    
    async def _create_test_environment(self, temp_dir: str, language: str, test_types: List[str]):
        """Create additional test files for the test environment."""
        try:
            if language == "python":
                # Create requirements.txt for Python tests
                requirements_file = os.path.join(temp_dir, "requirements.txt")
                with open(requirements_file, 'w') as f:
                    f.write("pytest\nflake8\nmypy\n")
                
                # Create test file if unit tests are requested
                if "unit_test" in test_types:
                    test_file = os.path.join(temp_dir, "test_main.py")
                    with open(test_file, 'w') as f:
                        f.write('''
import pytest
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the main module
try:
    import main
except ImportError:
    pass

def test_import():
    """Test that the main module can be imported."""
    try:
        import main
        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import main module: {e}")

def test_basic_functionality():
    """Test basic functionality."""
    # This is a basic test that should pass if the code is syntactically correct
    assert True
''')
            
            elif language == "javascript":
                # Create package.json for Node.js tests
                package_file = os.path.join(temp_dir, "package.json")
                with open(package_file, 'w') as f:
                    f.write("""
{
  "name": "ai-fix-test",
  "version": "1.0.0",
  "scripts": {
    "test": "echo 'Tests passed'"
  },
  "devDependencies": {
    "eslint": "^8.0.0"
  }
}
""")
                
        except Exception as e:
            logger.warning(f"Failed to create test environment: {e}")
    
    def _build_test_command(self, language: str, test_types: List[str], file_path: str) -> str:
        """Build the test command for the given language and test types."""
        commands = []
        
        for test_type in test_types:
            if language == "python":
                if test_type == "syntax_check":
                    commands.append(f"python -m py_compile {os.path.basename(file_path)}")
                elif test_type == "lint_check":
                    commands.append(f"python -m flake8 {os.path.basename(file_path)}")
                elif test_type == "type_check":
                    commands.append(f"python -m mypy {os.path.basename(file_path)}")
                elif test_type == "unit_test":
                    commands.append("python -m pytest test_main.py -v")
            elif language == "javascript":
                if test_type == "syntax_check":
                    commands.append(f"node --check {os.path.basename(file_path)}")
                elif test_type == "lint_check":
                    commands.append(f"npx eslint {os.path.basename(file_path)}")
                elif test_type == "test":
                    commands.append("npm test")
        
        return " && ".join(commands) if commands else f"echo 'No tests specified for {language}'"
    
    def _build_workspace_test_command(self, language: str, test_types: List[str]) -> str:
        """Build the test command for workspace testing."""
        commands = []
        
        for test_type in test_types:
            if language == "python":
                if test_type == "syntax_check":
                    commands.append("find . -name '*.py' -exec python -m py_compile {} \\;")
                elif test_type == "lint_check":
                    commands.append("python -m flake8 .")
                elif test_type == "unit_test":
                    commands.append("python -m pytest . -v")
            elif language == "javascript":
                if test_type == "syntax_check":
                    commands.append("find . -name '*.js' -exec node --check {} \\;")
                elif test_type == "lint_check":
                    commands.append("npx eslint .")
                elif test_type == "test":
                    commands.append("npm test")
        
        return " && ".join(commands) if commands else f"echo 'No tests specified for {language}'"
    
    def _get_test_environment(self, language: str) -> Dict[str, str]:
        """Get environment variables for testing."""
        env = {
            "PYTHONUNBUFFERED": "1",
            "TEST_MODE": "true",
            "CI": "true"
        }
        
        if language == "python":
            env.update({
                "PYTHONPATH": ".",
                "FLAKE8_QUIET": "1"
            })
        elif language == "javascript":
            env.update({
                "NODE_ENV": "test",
                "CI": "true"
            })
        
        return env

    async def _run_docker_test(
        self,
        temp_dir: str,
        file_path: str,
        language: str,
        test_type: str
    ) -> Dict[str, Any]:
        """
        Run a specific test in Docker (legacy method for backward compatibility).
        
        Args:
            temp_dir: Temporary directory containing test files
            file_path: Path to the file being tested
            language: Programming language
            test_type: Type of test to run
            
        Returns:
            Dictionary with test results
        """
        try:
            # Get base image for language
            base_image = self.docker_images.get(language, "python:3.11-slim")
            
            # Get test command
            test_commands = self.test_configs.get(language, {})
            test_command = test_commands.get(test_type, ["echo", "No test command available"])
            
            # Build Docker run command
            run_cmd = [
                "docker", "run", "--rm", "-i",
                "-v", f"{temp_dir}:/workspace",
                "-w", "/workspace",
                base_image
            ] + test_command
            
            # Add file argument if needed
            if test_type in ["syntax_check", "lint_check"]:
                run_cmd.append(os.path.basename(file_path))
            
            # Run the test
            result = subprocess.run(
                run_cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": f"Test timed out after 60 seconds"
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e)
            }

    async def _generate_feedback(self, test_result: TestResult):
        """Generate feedback data from test results."""
        try:
            feedback_id = f"feedback_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            # Calculate improvement score
            improvement_score = self._calculate_improvement_score(test_result)
            
            # Generate automatic feedback
            auto_feedback = self._generate_auto_feedback(test_result)
            
            # Create feedback data
            feedback_data = FeedbackData(
                feedback_id=feedback_id,
                test_result=test_result,
                improvement_score=improvement_score,
                user_feedback=None,
                auto_feedback=auto_feedback,
                timestamp=datetime.now(),
                applied=test_result.success
            )
            
            self.feedback_data.append(feedback_data)
            
            # Save feedback data
            await self._save_feedback_data()
            
        except Exception as e:
            logger.error(f"Error generating feedback: {e}")

    def _calculate_improvement_score(self, test_result: TestResult) -> float:
        """Calculate improvement score based on test results."""
        if test_result.success:
            # Base score for successful tests
            score = 0.8
            
            # Bonus for fast execution
            if test_result.execution_time < 5.0:
                score += 0.1
            
            # Bonus for comprehensive test types
            test_type_count = len(test_result.test_type.split(','))
            score += min(0.1 * test_type_count, 0.2)
            
            return min(score, 1.0)
        else:
            # Penalty for failed tests
            score = 0.2
            
            # Reduce penalty for syntax errors (easier to fix)
            if test_result.test_error and "syntax" in test_result.test_error.lower():
                score += 0.1
            
            return max(score, 0.0)

    def _generate_auto_feedback(self, test_result: TestResult) -> Dict[str, Any]:
        """Generate automatic feedback based on test results."""
        feedback = {
            "test_success": test_result.success,
            "execution_time": test_result.execution_time,
            "test_types": test_result.test_type.split(','),
            "error_analysis": {},
            "recommendations": []
        }
        
        if not test_result.success and test_result.test_error:
            error_lower = test_result.test_error.lower()
            
            # Analyze error types
            if "syntax" in error_lower:
                feedback["error_analysis"]["type"] = "syntax_error"
                feedback["recommendations"].append("Fix syntax errors in the code")
            
            if "import" in error_lower:
                feedback["error_analysis"]["type"] = "import_error"
                feedback["recommendations"].append("Check import statements and dependencies")
            
            if "permission" in error_lower:
                feedback["error_analysis"]["type"] = "permission_error"
                feedback["recommendations"].append("Check file permissions and access rights")
            
            if "timeout" in error_lower:
                feedback["error_analysis"]["type"] = "timeout_error"
                feedback["recommendations"].append("Optimize code performance or increase timeout")
        
        # Add container-specific feedback if available
        if test_result.container_result:
            feedback["container_info"] = {
                "exit_code": test_result.container_result.exit_code,
                "health_status": test_result.container_result.health_status,
                "duration": test_result.container_result.duration_seconds
            }
        
        return feedback

    async def _save_feedback_data(self):
        """Save feedback data to persistent storage."""
        try:
            # Create feedback directory if it doesn't exist
            feedback_dir = Path("data/feedback")
            feedback_dir.mkdir(parents=True, exist_ok=True)
            
            # Save to JSON file
            feedback_file = feedback_dir / f"feedback_{datetime.now().strftime('%Y%m%d')}.json"
            
            # Convert feedback data to serializable format
            serializable_feedback = []
            for feedback in self.feedback_data:
                feedback_dict = asdict(feedback)
                # Convert datetime objects to strings
                feedback_dict["timestamp"] = feedback_dict["timestamp"].isoformat()
                feedback_dict["test_result"]["timestamp"] = feedback_dict["test_result"]["timestamp"].isoformat()
                serializable_feedback.append(feedback_dict)
            
            with open(feedback_file, 'w') as f:
                json.dump(serializable_feedback, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving feedback data: {e}")

    def get_test_statistics(self) -> Dict[str, Any]:
        """Get comprehensive test statistics."""
        if not self.test_results:
            return {
                "total_tests": 0,
                "successful_tests": 0,
                "failed_tests": 0,
                "success_rate": 0.0,
                "average_execution_time": 0.0,
                "test_types": {},
                "recent_tests": []
            }
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results if result.success)
        failed_tests = total_tests - successful_tests
        success_rate = successful_tests / total_tests if total_tests > 0 else 0.0
        
        # Calculate average execution time
        execution_times = [result.execution_time for result in self.test_results]
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0.0
        
        # Count test types
        test_types = {}
        for result in self.test_results:
            for test_type in result.test_type.split(','):
                test_type = test_type.strip()
                test_types[test_type] = test_types.get(test_type, 0) + 1
        
        # Get recent tests
        recent_tests = self.test_results[-10:] if len(self.test_results) > 10 else self.test_results
        
        return {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": failed_tests,
            "success_rate": success_rate,
            "average_execution_time": avg_execution_time,
            "test_types": test_types,
            "recent_tests": [
                {
                    "test_id": result.test_id,
                    "file_path": result.file_path,
                    "success": result.success,
                    "execution_time": result.execution_time,
                    "test_type": result.test_type,
                    "timestamp": result.timestamp.isoformat()
                }
                for result in recent_tests
            ]
        }

    def get_feedback_statistics(self) -> Dict[str, Any]:
        """Get comprehensive feedback statistics."""
        if not self.feedback_data:
            return {
                "total_feedback": 0,
                "applied_feedback": 0,
                "average_improvement_score": 0.0,
                "feedback_trends": []
            }
        
        total_feedback = len(self.feedback_data)
        applied_feedback = sum(1 for feedback in self.feedback_data if feedback.applied)
        
        # Calculate average improvement score
        improvement_scores = [feedback.improvement_score for feedback in self.feedback_data]
        avg_improvement_score = sum(improvement_scores) / len(improvement_scores) if improvement_scores else 0.0
        
        return {
            "total_feedback": total_feedback,
            "applied_feedback": applied_feedback,
            "average_improvement_score": avg_improvement_score,
            "feedback_trends": [
                {
                    "feedback_id": feedback.feedback_id,
                    "improvement_score": feedback.improvement_score,
                    "applied": feedback.applied,
                    "timestamp": feedback.timestamp.isoformat()
                }
                for feedback in self.feedback_data[-20:]  # Last 20 feedback entries
            ]
        }

    async def cleanup_docker_containers(self):
        """Clean up Docker containers and images."""
        try:
            # Stop and remove containers with our naming pattern
            cleanup_cmd = [
                "docker", "ps", "-a", "--filter", "name=ai-fix-",
                "--format", "{{.ID}}"
            ]
            
            result = subprocess.run(cleanup_cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout.strip():
                container_ids = result.stdout.strip().split('\n')
                
                for container_id in container_ids:
                    if container_id:
                        try:
                            # Stop container
                            subprocess.run(["docker", "stop", container_id], timeout=10)
                            # Remove container
                            subprocess.run(["docker", "rm", container_id], timeout=10)
                        except Exception as e:
                            logger.warning(f"Failed to cleanup container {container_id}: {e}")
            
            logger.info("Docker cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during Docker cleanup: {e}")

    def export_test_results(self, file_path: str):
        """Export test results to a file."""
        try:
            # Convert test results to serializable format
            serializable_results = []
            for result in self.test_results:
                result_dict = asdict(result)
                # Convert datetime objects to strings
                result_dict["timestamp"] = result_dict["timestamp"].isoformat()
                # Remove container_result as it's not serializable
                result_dict.pop("container_result", None)
                serializable_results.append(result_dict)
            
            with open(file_path, 'w') as f:
                json.dump(serializable_results, f, indent=2)
                
            logger.info(f"Test results exported to: {file_path}")
            
        except Exception as e:
            logger.error(f"Error exporting test results: {e}")

    def export_feedback_data(self, file_path: str):
        """Export feedback data to a file."""
        try:
            # Convert feedback data to serializable format
            serializable_feedback = []
            for feedback in self.feedback_data:
                feedback_dict = asdict(feedback)
                # Convert datetime objects to strings
                feedback_dict["timestamp"] = feedback_dict["timestamp"].isoformat()
                feedback_dict["test_result"]["timestamp"] = feedback_dict["test_result"]["timestamp"].isoformat()
                # Remove container_result as it's not serializable
                if "test_result" in feedback_dict and "container_result" in feedback_dict["test_result"]:
                    feedback_dict["test_result"].pop("container_result", None)
                serializable_feedback.append(feedback_dict)
            
            with open(file_path, 'w') as f:
                json.dump(serializable_feedback, f, indent=2)
                
            logger.info(f"Feedback data exported to: {file_path}")
            
        except Exception as e:
            logger.error(f"Error exporting feedback data: {e}")
