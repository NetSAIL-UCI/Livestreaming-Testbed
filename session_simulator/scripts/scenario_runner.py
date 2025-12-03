#!/usr/bin/env python3
"""
Scenario Runner - Executes streaming session scenarios.

Reads a scenario YAML file and orchestrates:
1. Network profile application
2. Media server startup
3. Client instructions
4. Metrics collection
"""

import os
import sys
import yaml
import json
import argparse
import subprocess
import time
from pathlib import Path
from datetime import datetime


def load_scenario(scenario_file):
    """Load and validate scenario YAML file."""
    try:
        with open(scenario_file, 'r') as f:
            scenario = yaml.safe_load(f)
        return scenario
    except Exception as e:
        print(f"ERROR: Failed to load scenario file: {e}")
        sys.exit(1)


def validate_scenario(scenario):
    """Basic validation of scenario structure."""
    required_fields = ['id', 'protocol', 'mpd_url', 'network_profile', 'experiment']
    for field in required_fields:
        if field not in scenario:
            print(f"ERROR: Missing required field: {field}")
            sys.exit(1)
    
    if scenario['network_profile']['type'] not in ['static', 'trace']:
        print(f"ERROR: Invalid network_profile.type: {scenario['network_profile']['type']}")
        sys.exit(1)
    
    if scenario['protocol'] not in ['dash', 'lldash', 'webrtc', 'moq']:
        print(f"WARNING: Protocol {scenario['protocol']} may not be fully implemented")


def apply_network_profile(network_profile, traffic_shaper_container):
    """
    Apply network profile to traffic shaper container.
    
    Args:
        network_profile: Network profile dict from scenario
        traffic_shaper_container: Name of traffic shaper container
    """
    profile_type = network_profile['type']
    profile_file = network_profile.get('file')
    
    if not profile_file:
        print("WARNING: No profile file specified, using passthrough")
        return
    
    # Resolve absolute path
    profile_path = os.path.abspath(profile_file)
    
    if not os.path.exists(profile_path):
        print(f"ERROR: Profile file not found: {profile_path}")
        sys.exit(1)
    
    # Map to container path (files are mounted in /app/config and /app/traces)
    # Determine if it's a config or trace file
    profile_abs = os.path.abspath(profile_path)
    testbed_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    network_emulation_root = os.path.join(testbed_root, 'network_emulation')
    
    if profile_abs.startswith(os.path.join(network_emulation_root, 'config')):
        # Config file - map to /app/config
        rel_path = os.path.relpath(profile_abs, os.path.join(network_emulation_root, 'config'))
        container_path = f"/app/config/{rel_path}"
    elif profile_abs.startswith(os.path.join(network_emulation_root, 'traces')):
        # Trace file - map to /app/traces
        rel_path = os.path.relpath(profile_abs, os.path.join(network_emulation_root, 'traces'))
        container_path = f"/app/traces/{rel_path}"
    else:
        # Try to copy file into container or use direct path
        # For now, assume it's accessible via volume mount
        container_path = profile_path
    
    print(f"Applying {profile_type} network profile: {profile_path} -> {container_path}")
    
    if profile_type == 'static':
        # Apply static profile
        cmd = [
            'docker', 'exec', traffic_shaper_container,
            'python3', '/app/scripts/apply_static_profile.py',
            container_path
        ]
    elif profile_type == 'trace':
        # Start trace replay in background
        cmd = [
            'docker', 'exec', '-d', traffic_shaper_container,
            'python3', '/app/scripts/replay_trace.py',
            container_path
        ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"✓ Network profile applied")
        if result.stdout:
            print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to apply network profile: {e}")
        print(e.stderr)
        sys.exit(1)


def create_result_directory(scenario, base_results_dir):
    """
    Create result directory for experiment.
    
    Returns:
        Path to result directory
    """
    experiment_id = scenario['id']
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_id = f"{experiment_id}_{timestamp}"
    
    result_dir = os.path.join(base_results_dir, run_id)
    os.makedirs(result_dir, exist_ok=True)
    
    # Create subdirectories
    os.makedirs(os.path.join(result_dir, 'stats'), exist_ok=True)
    os.makedirs(os.path.join(result_dir, 'logs'), exist_ok=True)
    
    # Copy scenario file to results
    scenario_copy = os.path.join(result_dir, 'scenario.yaml')
    import shutil
    shutil.copy(scenario['_source_file'], scenario_copy)
    
    return result_dir, run_id


def export_metrics(experiment_id, stats_server_container, result_dir):
    """
    Export metrics from MongoDB to JSON file.
    
    Args:
        experiment_id: Experiment identifier
        stats_server_container: Name of stats server container
        result_dir: Result directory path
    """
    print(f"Exporting metrics for experiment: {experiment_id}")
    
    # Use Python script inside stats_server container to export
    export_script = f"""
from storage import MetricsStorage
import json
import sys

storage = MetricsStorage()
metrics = storage.get_metrics('{experiment_id}')

# Convert ObjectId to string
for metric in metrics:
    if '_id' in metric:
        metric['_id'] = str(metric['_id'])

output_file = '/tmp/metrics_export.json'
with open(output_file, 'w') as f:
    json.dump(metrics, f, indent=2, default=str)

print(f'Exported {{len(metrics)}} metrics to {{output_file}}')
"""
    
    # Write script to temp file
    script_file = '/tmp/export_metrics.py'
    with open(script_file, 'w') as f:
        f.write(export_script)
    
    # Copy script to container and execute
    try:
        subprocess.run([
            'docker', 'cp', script_file, f'{stats_server_container}:/tmp/export_metrics.py'
        ], check=True)
        
        result = subprocess.run([
            'docker', 'exec', stats_server_container,
            'python3', '/tmp/export_metrics.py'
        ], capture_output=True, text=True, check=True)
        
        # Copy exported file back
        subprocess.run([
            'docker', 'cp', f'{stats_server_container}:/tmp/metrics_export.json',
            os.path.join(result_dir, 'stats', 'metrics.json')
        ], check=True)
        
        print(f"✓ Metrics exported to {result_dir}/stats/metrics.json")
        print(result.stdout)
        
    except subprocess.CalledProcessError as e:
        print(f"WARNING: Failed to export metrics: {e}")
        print(e.stderr)


def main():
    parser = argparse.ArgumentParser(description="Run streaming session scenario")
    parser.add_argument("scenario_file", help="Path to scenario YAML file")
    parser.add_argument("--server-ip", help="Server public IP address", required=True)
    parser.add_argument("--stats-port", help="Stats server port", default=8000, type=int)
    parser.add_argument("--results-dir", help="Base results directory", 
                       default="../../experiments/results")
    parser.add_argument("--traffic-shaper", help="Traffic shaper container name",
                       default="traffic_shaper")
    parser.add_argument("--stats-server", help="Stats server container name",
                       default="stats_server")
    parser.add_argument("--skip-network", action="store_true",
                       help="Skip network profile application")
    parser.add_argument("--skip-export", action="store_true",
                       help="Skip metrics export")
    
    args = parser.parse_args()
    
    # Load scenario
    scenario = load_scenario(args.scenario_file)
    scenario['_source_file'] = args.scenario_file  # Store source for copying
    validate_scenario(scenario)
    
    print(f"=== Running Scenario: {scenario['id']} ===")
    print(f"Protocol: {scenario['protocol']}")
    print(f"Duration: {scenario['experiment']['duration_s']}s")
    
    # Create result directory
    result_dir, run_id = create_result_directory(scenario, args.results_dir)
    print(f"Result directory: {result_dir}")
    
    # Apply network profile
    if not args.skip_network:
        apply_network_profile(scenario['network_profile'], args.traffic_shaper)
    else:
        print("Skipping network profile application")
    
    # Generate client URL
    mpd_url = scenario['mpd_url'].replace('SERVER_PUBLIC_IP', args.server_ip)
    stats_server_url = f"http://{args.server_ip}:{args.stats_port}"
    
    client_url = (
        f"file://{os.path.abspath('../../protocol_integration/dash/client_examples/dash_player.html')}"
        f"?mpd={mpd_url}"
        f"&stats_server={stats_server_url}"
        f"&experiment_id={scenario['id']}"
    )
    
    print("\n" + "="*60)
    print("CLIENT INSTRUCTIONS:")
    print("="*60)
    print(f"1. Open the DASH player in your browser:")
    print(f"   {client_url}")
    print(f"\n2. Click 'Load Player' to start playback")
    print(f"\n3. Experiment will run for {scenario['experiment']['duration_s']} seconds")
    print(f"\n4. Wait for the experiment to complete...")
    print("="*60 + "\n")
    
    # Wait for experiment duration
    duration = scenario['experiment']['duration_s']
    print(f"Waiting {duration} seconds for experiment to complete...")
    time.sleep(duration)
    
    # Export metrics
    if not args.skip_export:
        export_metrics(scenario['id'], args.stats_server, result_dir)
    else:
        print("Skipping metrics export")
    
    print(f"\n✓ Experiment complete!")
    print(f"Results saved to: {result_dir}")


if __name__ == "__main__":
    main()

