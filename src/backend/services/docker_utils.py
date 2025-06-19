import subprocess
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
    cmd = ["docker", "build", "-t", tag]
    if dockerfile_path:
        cmd += ["-f", dockerfile_path]
    if build_args:
        for k, v in build_args.items():
            cmd += ["--build-arg", f"{k}={v}"]
    cmd.append(context_dir)
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
    cmd = ["docker", "run"]
    if detach:
        cmd.append("-d")
    if run_args:
        cmd += run_args
    if volumes:
        for host_path, container_path in volumes.items():
            cmd += ["-v", f"{host_path}:{container_path}"]
    if env_vars:
        for k, v in env_vars.items():
            cmd += ["-e", f"{k}={v}"]
    cmd.append(image)
    if command:
        cmd += command
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
    tag = "ai-coder-app:latest"
    build_success, build_output = build_docker_image(context_dir, dockerfile_path, None, tag)
    if not build_success:
        return {"success": False, "stage": "build", "output": build_output}
    run_args = run_opts.split() if run_opts else []
    command = test_command.split()
    run_success, run_output = run_docker_container(tag, run_args, command)
    return {"success": run_success, "stage": "test", "output": run_output} 