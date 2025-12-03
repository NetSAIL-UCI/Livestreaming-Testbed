"""
Docker utility functions.
"""

import subprocess
import json


def check_containers_running(container_names):
    """
    Check if specified containers are running.
    
    Args:
        container_names: List of container names to check
    
    Returns:
        True if all containers are running, False otherwise
    """
    try:
        result = subprocess.run(
            ['docker', 'ps', '--format', '{{.Names}}'],
            capture_output=True,
            text=True,
            check=True
        )
        running_containers = set(result.stdout.strip().split('\n'))
        
        for name in container_names:
            if name not in running_containers:
                print(f"Container '{name}' is not running")
                return False
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to check containers: {e}")
        return False


def get_container_name(service_name, compose_file=None):
    """
    Get the actual container name for a service.
    
    Args:
        service_name: Docker Compose service name
        compose_file: Path to docker-compose file (optional)
    
    Returns:
        Container name or None if not found
    """
    try:
        cmd = ['docker', 'ps', '--format', '{{.Names}}', '--filter', f'name={service_name}']
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        names = result.stdout.strip().split('\n')
        return names[0] if names else None
    except subprocess.CalledProcessError:
        return None


def exec_in_container(container_name, command):
    """
    Execute a command in a container.
    
    Args:
        container_name: Name of the container
        command: Command to execute (list of strings)
    
    Returns:
        subprocess.CompletedProcess result
    """
    cmd = ['docker', 'exec', container_name] + command
    return subprocess.run(cmd, capture_output=True, text=True)

