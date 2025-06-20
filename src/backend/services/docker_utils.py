import subprocess
import shlex
from typing import Optional, Dict, List, Tuple

def build_docker_image(
    context_dir: str,
    dockerfile_path: Optional[str] = None,
    build_args: Optional[Dict[str, str]] = None,
    tag: str = "ai-coder-app:latest"
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
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def run_docker_container(
    image: str,
    run_args: Optional[List[str]] = None,
    command: Optional[List[str]] = None,
    volumes: Optional[Dict[str, str]] = None,
    env_vars: Optional[Dict[str, str]] = None,
    detach: bool = False
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
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def run_build_and_test_in_docker(
    context_dir: str,
    dockerfile_path: str = None,
    build_args: str = "",
    run_opts: str = "",
    test_command: str = "python run_tests.py"
) -> dict:
    """
    Build the Docker image and run tests in a container. Returns a dict with success, stage, and output.
    """
    # Sanitize inputs to prevent command injection
    sanitized_context_dir = shlex.quote(context_dir)
    sanitized_dockerfile_path = shlex.quote(dockerfile_path) if dockerfile_path else None
    sanitized_build_args = shlex.quote(build_args) if build_args else ""
    sanitized_run_opts = shlex.quote(run_opts) if run_opts else ""
    sanitized_test_command = shlex.quote(test_command) if test_command else "python run_tests.py"
    
    tag = "ai-coder-app:latest"
    build_success, build_output = build_docker_image(sanitized_context_dir, sanitized_dockerfile_path, None, tag)
    if not build_success:
        return {"success": False, "stage": "build", "output": build_output}
    run_args = sanitized_run_opts.split() if sanitized_run_opts else []
    command = sanitized_test_command.split()
    run_success, run_output = run_docker_container(tag, run_args, command)
    return {"success": run_success, "stage": "test", "output": run_output} 