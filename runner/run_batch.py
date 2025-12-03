#!/usr/bin/env python3
"""
Batch experiment runner.

Runs multiple scenarios sequentially.
"""

import os
import sys
import argparse
import glob
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Run batch of streaming experiments")
    parser.add_argument("scenario_dir", help="Directory containing scenario YAML files")
    parser.add_argument("--server-ip", help="Server public IP address", required=True)
    parser.add_argument("--stats-port", help="Stats server port", default=8000, type=int)
    parser.add_argument("--results-dir", help="Base results directory",
                       default="../../experiments/results")
    parser.add_argument("--pattern", help="File pattern to match", default="*.yaml")
    parser.add_argument("--stop-on-error", action="store_true",
                       help="Stop batch on first error")
    
    args = parser.parse_args()
    
    # Find scenario files
    pattern = os.path.join(args.scenario_dir, args.pattern)
    scenario_files = sorted(glob.glob(pattern))
    
    if not scenario_files:
        print(f"ERROR: No scenario files found matching {pattern}")
        sys.exit(1)
    
    print(f"Found {len(scenario_files)} scenario files")
    
    # Run each scenario
    run_experiment = os.path.join(os.path.dirname(__file__), 'run_experiment.py')
    
    results = []
    for i, scenario_file in enumerate(scenario_files, 1):
        print(f"\n{'='*60}")
        print(f"Running scenario {i}/{len(scenario_files)}: {scenario_file}")
        print(f"{'='*60}\n")
        
        cmd = [
            'python3', run_experiment,
            scenario_file,
            '--server-ip', args.server_ip,
            '--stats-port', str(args.stats_port),
            '--results-dir', args.results_dir
        ]
        
        result = subprocess.run(cmd)
        results.append((scenario_file, result.returncode))
        
        if result.returncode != 0:
            print(f"\nERROR: Scenario {scenario_file} failed")
            if args.stop_on_error:
                print("Stopping batch due to error")
                break
    
    # Summary
    print(f"\n{'='*60}")
    print("Batch Execution Summary")
    print(f"{'='*60}")
    successful = sum(1 for _, code in results if code == 0)
    failed = len(results) - successful
    
    for scenario_file, code in results:
        status = "✓" if code == 0 else "✗"
        print(f"{status} {scenario_file}")
    
    print(f"\nTotal: {len(results)}, Successful: {successful}, Failed: {failed}")


if __name__ == "__main__":
    main()

