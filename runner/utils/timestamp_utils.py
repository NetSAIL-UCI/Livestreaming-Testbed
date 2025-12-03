"""
Timestamp utility functions.
"""

from datetime import datetime


def generate_run_id(experiment_id):
    """
    Generate a unique run ID with timestamp.
    
    Args:
        experiment_id: Base experiment identifier
    
    Returns:
        Run ID string (e.g., "exp_001_20240101_120000")
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{experiment_id}_{timestamp}"


def get_timestamp():
    """Get current timestamp as ISO string."""
    return datetime.now().isoformat()


def parse_timestamp(timestamp_str):
    """Parse timestamp string to datetime object."""
    return datetime.fromisoformat(timestamp_str)

