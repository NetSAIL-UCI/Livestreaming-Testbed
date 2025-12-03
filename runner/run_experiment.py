#!/usr/bin/env python3
"""
Main experiment runner script.

Orchestrates the execution of a single experiment scenario.
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

# Add utils to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'utils'))

from docker_utils import check_containers_running, get_container_name
from timestamp_utils import generate_run_id
from logging_utils import setup_logging


def main():
    parser = argparse.ArgumentParser(description="Run a streaming experiment")
    parser.add_argument("scenario_file", help="Path to scenario YAML file")
    parser.add_argument("--server-ip", help="Server public IP address", required=True)
    parser.add_argument("--stats-port", help="Stats server port", default=8000, type=int)
    parser.add_argument("--results-dir", help="Base results directory",
                       default="../../experiments/results")
    parser.add_argument("--compose-file", help="Docker Compose file",
                       default="../../docker-compose-emulation.yaml")
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging()
    logger.info("=== Experiment Runner Starting ===")
    
    # Check if containers are running
    required_containers = ['traffic_shaper', 'dash_media_server', 'stats_server', 'mongo']
    if not check_containers_running(required_containers):
        logger.error("Required containers are not running. Please start them with docker-compose.")
        sys.exit(1)
    
    logger.info("All required containers are running")
    
    # Run scenario runner
    scenario_runner = os.path.join(
        os.path.dirname(__file__),
        '../../session_simulator/scripts/scenario_runner.py'
    )
    
    cmd = [
        'python3', scenario_runner,
        args.scenario_file,
        '--server-ip', args.server_ip,
        '--stats-port', str(args.stats_port),
        '--results-dir', args.results_dir
    ]
    
    logger.info(f"Executing scenario: {args.scenario_file}")
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        logger.info("Experiment completed successfully")
    else:
        logger.error("Experiment failed")
        sys.exit(result.returncode)


if __name__ == "__main__":
    main()

