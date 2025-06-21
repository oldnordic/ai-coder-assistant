import shlex
import subprocess
import time
import logging
import json
import os
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ContainerTestResult:
    """Result of a container test."""
    success: bool
    container_id: Optional[str] = None
    logs: str = ""
    exit_code: Optional[int] = None
    duration_seconds: float = 0.0
    error_message: Optional[str] = None
    health_status: Optional[str] = None
    test_output: Optional[str] = None


@dataclass
class DockerTestConfig:
    """Configuration for Docker testing."""
    image_tag: str = "ai-fix-test"
    container_name: str = "ai-fix-container"
    timeout_seconds: int = 300
    health_check_interval: int = 5
    max_health_checks: int = 60
    cleanup_on_failure: bool = True
    preserve_logs: bool = True
    test_command: Optional[str] = None
    environment_vars: Optional[Dict[str, str]] = None
    volumes: Optional[Dict[str, str]] = None
    ports: Optional[Dict[str, str]] = None


class DockerUtils:
    """Enhanced Docker utilities for test and feedback loop."""
    
    @staticmethod
    def build_image_for_testing(
        context_dir: str,
        dockerfile_path: Optional[str] = None,
        build_args: Optional[Dict[str, str]] = None,
        tag: str = "ai-fix-test",
        timeout: int = 600
    ) -> Tuple[bool, str]:
        """
        Build a Docker image specifically for testing fixes.
        
        Args:
            context_dir: Directory containing the code to test
            dockerfile_path: Path to Dockerfile (optional)
            build_args: Build arguments for Docker
            tag: Image tag
            timeout: Build timeout in seconds
            
        Returns:
            Tuple of (success, output)
        """
        logger.info(f"Building Docker image for testing: {tag}")
        
        # Add test-specific build args
        if build_args is None:
            build_args = {}
        
        # Ensure we have test environment
        build_args.update({
            "TEST_MODE": "true",
            "BUILD_DATE": datetime.now().isoformat()
        })
        
        return build_docker_image(
            context_dir=context_dir,
            dockerfile_path=dockerfile_path,
            build_args=build_args,
            tag=tag,
            timeout=timeout
        )
    
    @staticmethod
    def run_container_with_monitoring(
        config: DockerTestConfig,
        log_callback: Optional[Callable[[str], None]] = None
    ) -> ContainerTestResult:
        """
        Run a container with comprehensive monitoring and health checks.
        
        Args:
            config: Docker test configuration
            log_callback: Optional callback for real-time log streaming
            
        Returns:
            ContainerTestResult with detailed test information
        """
        start_time = time.time()
        container_id = None
        
        try:
            logger.info(f"Starting container test: {config.container_name}")
            
            # Build run command
            run_cmd = ["docker", "run", "--name", config.container_name]
            
            # Add detach flag for monitoring
            run_cmd.append("-d")
            
            # Add environment variables
            if config.environment_vars:
                for key, value in config.environment_vars.items():
                    run_cmd.extend(["-e", f"{key}={value}"])
            
            # Add volume mounts
            if config.volumes:
                for host_path, container_path in config.volumes.items():
                    run_cmd.extend(["-v", f"{host_path}:{container_path}"])
            
            # Add port mappings
            if config.ports:
                for host_port, container_port in config.ports.items():
                    run_cmd.extend(["-p", f"{host_port}:{container_port}"])
            
            # Add image and command
            run_cmd.append(config.image_tag)
            
            if config.test_command:
                run_cmd.extend(config.test_command.split())
            
            # Start container
            result = subprocess.run(run_cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return ContainerTestResult(
                    success=False,
                    error_message=f"Failed to start container: {result.stderr}",
                    duration_seconds=time.time() - start_time
                )
            
            container_id = result.stdout.strip()
            logger.info(f"Container started: {container_id}")
            
            # Monitor container and collect logs
            logs, exit_code, health_status = DockerUtils._monitor_container(
                container_id, config, log_callback
            )
            
            duration = time.time() - start_time
            
            # Determine success based on exit code and logs
            success = exit_code == 0 and not DockerUtils._logs_indicate_failure(logs)
            
            return ContainerTestResult(
                success=success,
                container_id=container_id,
                logs=logs,
                exit_code=exit_code,
                duration_seconds=duration,
                health_status=health_status,
                test_output=logs if success else None
            )
            
        except subprocess.TimeoutExpired:
            error_msg = f"Container test timed out after {config.timeout_seconds} seconds"
            logger.error(error_msg)
            return ContainerTestResult(
                success=False,
                container_id=container_id,
                error_message=error_msg,
                duration_seconds=time.time() - start_time
            )
            
        except Exception as e:
            error_msg = f"Container test failed: {str(e)}"
            logger.error(error_msg)
            return ContainerTestResult(
                success=False,
                container_id=container_id,
                error_message=error_msg,
                duration_seconds=time.time() - start_time
            )
            
        finally:
            # Cleanup if configured
            if config.cleanup_on_failure or (container_id and not config.preserve_logs):
                DockerUtils._cleanup_container(container_id, config.container_name)
    
    @staticmethod
    def _monitor_container(
        container_id: str,
        config: DockerTestConfig,
        log_callback: Optional[Callable[[str], None]] = None
    ) -> Tuple[str, Optional[int], Optional[str]]:
        """
        Monitor container execution and collect logs.
        
        Returns:
            Tuple of (logs, exit_code, health_status)
        """
        logs = ""
        exit_code = None
        health_status = None
        
        # Monitor container for specified timeout
        start_time = time.time()
        health_checks = 0
        
        while time.time() - start_time < config.timeout_seconds:
            # Check if container is still running
            status_result = subprocess.run(
                ["docker", "inspect", "--format", "{{.State.Status}}", container_id],
                capture_output=True, text=True
            )
            
            if status_result.returncode != 0:
                break
            
            status = status_result.stdout.strip()
            
            # Collect logs
            log_result = subprocess.run(
                ["docker", "logs", container_id],
                capture_output=True, text=True
            )
            
            if log_result.returncode == 0:
                current_logs = log_result.stdout
                if current_logs != logs:
                    new_logs = current_logs[len(logs):]
                    logs = current_logs
                    
                    # Call log callback if provided
                    if log_callback and new_logs:
                        log_callback(new_logs)
            
            # Check health status
            if health_checks < config.max_health_checks:
                health_result = subprocess.run(
                    ["docker", "inspect", "--format", "{{.State.Health.Status}}", container_id],
                    capture_output=True, text=True
                )
                
                if health_result.returncode == 0:
                    health_status = health_result.stdout.strip()
                    health_checks += 1
            
            # Check if container has exited
            if status in ["exited", "dead"]:
                # Get exit code
                exit_code_result = subprocess.run(
                    ["docker", "inspect", "--format", "{{.State.ExitCode}}", container_id],
                    capture_output=True, text=True
                )
                
                if exit_code_result.returncode == 0:
                    try:
                        exit_code = int(exit_code_result.stdout.strip())
                    except ValueError:
                        exit_code = -1
                break
            
            time.sleep(config.health_check_interval)
        
        return logs, exit_code, health_status
    
    @staticmethod
    def _logs_indicate_failure(logs: str) -> bool:
        """
        Analyze logs to determine if they indicate a failure.
        
        Args:
            logs: Container logs to analyze
            
        Returns:
            True if logs indicate failure, False otherwise
        """
        if not logs:
            return False
        
        logs_lower = logs.lower()
        
        # Common failure indicators
        failure_indicators = [
            "error", "failed", "failure", "exception", "traceback",
            "segmentation fault", "core dumped", "killed",
            "timeout", "connection refused", "permission denied",
            "no such file", "import error", "syntax error",
            "runtime error", "assertion failed", "test failed"
        ]
        
        # Check for failure indicators
        for indicator in failure_indicators:
            if indicator in logs_lower:
                logger.warning(f"Logs indicate failure: found '{indicator}'")
                return True
        
        # Check for specific error patterns
        error_patterns = [
            r"error:\s*\d+",  # Error codes
            r"failed\s+with\s+exit\s+code",  # Exit code failures
            r"test.*failed",  # Test failures
            r"assert.*failed",  # Assertion failures
        ]
        
        import re
        for pattern in error_patterns:
            if re.search(pattern, logs_lower):
                logger.warning(f"Logs indicate failure: matched pattern '{pattern}'")
                return True
        
        return False
    
    @staticmethod
    def _cleanup_container(container_id: Optional[str], container_name: str):
        """Clean up container and related resources."""
        try:
            if container_id:
                # Stop container
                subprocess.run(["docker", "stop", container_id], capture_output=True, timeout=10)
                
                # Remove container
                subprocess.run(["docker", "rm", container_id], capture_output=True, timeout=10)
            else:
                # Try to remove by name
                subprocess.run(["docker", "rm", "-f", container_name], capture_output=True, timeout=10)
                
        except Exception as e:
            logger.warning(f"Failed to cleanup container {container_name}: {e}")
    
    @staticmethod
    def run_comprehensive_test(
        context_dir: str,
        test_config: DockerTestConfig,
        log_callback: Optional[Callable[[str], None]] = None
    ) -> ContainerTestResult:
        """
        Run a comprehensive test including build and execution.
        
        Args:
            context_dir: Directory containing code to test
            test_config: Test configuration
            log_callback: Optional callback for log streaming
            
        Returns:
            ContainerTestResult with test results
        """
        logger.info(f"Starting comprehensive test for: {context_dir}")
        
        # Step 1: Build image
        build_success, build_output = DockerUtils.build_image_for_testing(
            context_dir=context_dir,
            tag=test_config.image_tag,
            timeout=test_config.timeout_seconds
        )
        
        if not build_success:
            return ContainerTestResult(
                success=False,
                error_message=f"Build failed: {build_output}",
                duration_seconds=0.0
            )
        
        logger.info("Docker image built successfully")
        
        # Step 2: Run container test
        test_result = DockerUtils.run_container_with_monitoring(test_config, log_callback)
        
        # Step 3: Cleanup
        if test_config.cleanup_on_failure or not test_config.preserve_logs:
            DockerUtils._cleanup_container(test_result.container_id, test_config.container_name)
        
        return test_result
    
    @staticmethod
    def analyze_test_results(result: ContainerTestResult) -> Dict[str, any]:
        """
        Analyze test results and provide detailed feedback.
        
        Args:
            result: Container test result
            
        Returns:
            Dictionary with analysis results
        """
        analysis = {
            "overall_success": result.success,
            "duration_seconds": result.duration_seconds,
            "exit_code": result.exit_code,
            "health_status": result.health_status,
            "has_errors": False,
            "error_types": [],
            "recommendations": []
        }
        
        if not result.success:
            analysis["has_errors"] = True
            
            # Analyze logs for specific error types
            logs_lower = result.logs.lower()
            
            if "syntax error" in logs_lower:
                analysis["error_types"].append("syntax_error")
                analysis["recommendations"].append("Check code syntax and fix compilation errors")
            
            if "import error" in logs_lower:
                analysis["error_types"].append("import_error")
                analysis["recommendations"].append("Verify all dependencies are properly installed")
            
            if "permission denied" in logs_lower:
                analysis["error_types"].append("permission_error")
                analysis["recommendations"].append("Check file permissions and access rights")
            
            if "timeout" in logs_lower:
                analysis["error_types"].append("timeout_error")
                analysis["recommendations"].append("Consider increasing timeout or optimizing performance")
            
            if "connection refused" in logs_lower:
                analysis["error_types"].append("connection_error")
                analysis["recommendations"].append("Check network configuration and service availability")
            
            if "test failed" in logs_lower:
                analysis["error_types"].append("test_failure")
                analysis["recommendations"].append("Review test cases and fix failing assertions")
        
        return analysis


# Legacy functions for backward compatibility
def build_docker_image(
    context_dir: str,
    dockerfile_path: Optional[str] = None,
    build_args: Optional[Dict[str, str]] = None,
    tag: str = "ai-coder-app:latest",
    timeout: int = 600,  # 10-minute timeout
) -> Tuple[bool, str]:
    """
    Build a Docker image from the given context directory and Dockerfile.
    Returns (success, output).
    """
    # Sanitize inputs to prevent command injection
    sanitized_tag = shlex.quote(tag)
    sanitized_context_dir = shlex.quote(context_dir)

    cmd = ["docker", "build", "-t", sanitized_tag]
    if dockerfile_path:
        sanitized_dockerfile_path = shlex.quote(dockerfile_path)
        cmd += ["-f", sanitized_dockerfile_path]
    if build_args:
        for k, v in build_args.items():
            sanitized_key = shlex.quote(k)
            sanitized_value = shlex.quote(v)
            cmd += ["--build-arg", f"{sanitized_key}={sanitized_value}"]
    cmd.append(sanitized_context_dir)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=timeout)
        return True, result.stdout
    except subprocess.TimeoutExpired:
        return False, f"Docker build operation timed out after {timeout} seconds."
    except subprocess.CalledProcessError as e:
        return False, e.stderr


def run_docker_container(
    image: str,
    run_args: Optional[List[str]] = None,
    command: Optional[List[str]] = None,
    volumes: Optional[Dict[str, str]] = None,
    env_vars: Optional[Dict[str, str]] = None,
    detach: bool = False,
    timeout: int = 300,  # 5-minute timeout
) -> Tuple[bool, str]:
    """
    Run a Docker container from the given image with optional run args, command, volumes, and env vars.
    Returns (success, output or container id).
    """
    # Sanitize inputs to prevent command injection
    sanitized_image = shlex.quote(image)

    cmd = ["docker", "run"]
    if detach:
        cmd.append("-d")
    if run_args:
        sanitized_run_args = [shlex.quote(arg) for arg in run_args]
        cmd += sanitized_run_args
    if volumes:
        for host_path, container_path in volumes.items():
            sanitized_host_path = shlex.quote(host_path)
            sanitized_container_path = shlex.quote(container_path)
            cmd += ["-v", f"{sanitized_host_path}:{sanitized_container_path}"]
    if env_vars:
        for k, v in env_vars.items():
            sanitized_key = shlex.quote(k)
            sanitized_value = shlex.quote(v)
            cmd += ["-e", f"{sanitized_key}={sanitized_value}"]
    cmd.append(sanitized_image)
    if command:
        sanitized_command = [shlex.quote(arg) for arg in command]
        cmd += sanitized_command
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=timeout)
        return True, result.stdout.strip()
    except subprocess.TimeoutExpired:
        return False, f"Docker run operation timed out after {timeout} seconds."
    except subprocess.CalledProcessError as e:
        return False, e.stderr


def run_build_and_test_in_docker(
    context_dir: str,
    dockerfile_path: Optional[str] = None,
    build_args: str = "",
    run_opts: str = "",
    test_command: str = "python run_tests.py",
    build_timeout: int = 600,  # 10-minute build timeout
    test_timeout: int = 300,   # 5-minute test timeout
) -> Dict[str, str]:
    """
    Build the Docker image and run tests in a container. Returns a dict with success, stage, and output.
    """
    # Sanitize inputs to prevent command injection
    sanitized_context_dir = shlex.quote(context_dir)
    sanitized_dockerfile_path = (
        shlex.quote(dockerfile_path) if dockerfile_path else None
    )
    sanitized_run_opts = shlex.quote(run_opts) if run_opts else ""
    sanitized_test_command = (
        shlex.quote(test_command) if test_command else "python run_tests.py"
    )

    tag = "ai-coder-app:latest"
    build_success, build_output = build_docker_image(
        sanitized_context_dir, sanitized_dockerfile_path, None, tag, build_timeout
    )
    if not build_success:
        return {"success": "False", "stage": "build", "output": build_output}
    run_args = sanitized_run_opts.split() if sanitized_run_opts else []
    command = sanitized_test_command.split()
    run_success, run_output = run_docker_container(tag, run_args, command, timeout=test_timeout)
    return {"success": str(run_success), "stage": "test", "output": run_output}
