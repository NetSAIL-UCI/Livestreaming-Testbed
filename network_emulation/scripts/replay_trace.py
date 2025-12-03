#!/usr/bin/env python3
"""
Replay time-varying network trace using tc/netem.

Reads a CSV trace file and applies network conditions in real-time
according to the trace timestamps.
"""

import os
import sys
import csv
import time
import subprocess
import argparse
from datetime import datetime


def run_cmd(cmd, check=True):
    """Run a shell command and return the result."""
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True, check=check
    )
    return result.stdout.strip()


def apply_netem_config(interface, delay_ms=0, jitter_ms=0, loss_pct=0, rate_mbps=None):
    """Apply netem configuration to an interface."""
    # Clear existing rules
    run_cmd(f"tc qdisc del dev {interface} root", check=False)
    
    # Build netem command
    netem_params = []
    
    if delay_ms > 0 or jitter_ms > 0:
        if jitter_ms > 0:
            netem_params.append(f"delay {delay_ms}ms {jitter_ms}ms")
        else:
            netem_params.append(f"delay {delay_ms}ms")
    
    if loss_pct > 0:
        netem_params.append(f"loss {loss_pct}%")
    
    if rate_mbps:
        netem_params.append(f"rate {rate_mbps}mbit")
    
    # Apply configuration
    if netem_params:
        netem_str = " ".join(netem_params)
        run_cmd(f"tc qdisc add dev {interface} root handle 1: prio")
        run_cmd(f"tc qdisc add dev {interface} parent 1:1 handle 2: netem {netem_str}")
        run_cmd(f"tc filter add dev {interface} protocol ip parent 1:0 prio 1 u32 match ip dst 0.0.0.0/0 flowid 1:1")
    else:
        run_cmd(f"tc qdisc add dev {interface} root handle 1: prio")
        run_cmd(f"tc qdisc add dev {interface} parent 1:1 handle 2: netem delay 0ms")
        run_cmd(f"tc filter add dev {interface} protocol ip parent 1:0 prio 1 u32 match ip dst 0.0.0.0/0 flowid 1:1")


def parse_trace_file(trace_file):
    """
    Parse CSV trace file.
    
    Expected format:
    time_ms,delay_ms,loss_pct,rate_mbps
    0,50,0,10
    1000,100,1,5
    ...
    """
    trace_points = []
    
    with open(trace_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            trace_points.append({
                'time_ms': int(row.get('time_ms', 0)),
                'delay_ms': float(row.get('delay_ms', 0)),
                'jitter_ms': float(row.get('jitter_ms', 0)),
                'loss_pct': float(row.get('loss_pct', 0)),
                'rate_mbps': float(row.get('rate_mbps', 0)) if row.get('rate_mbps') else None
            })
    
    return trace_points


def main():
    parser = argparse.ArgumentParser(description="Replay network trace")
    parser.add_argument("trace_file", help="Path to CSV trace file")
    parser.add_argument("--interface", help="Interface to apply to (default: CLIENT_IF)", default=None)
    parser.add_argument("--start-time", help="Start time offset in seconds", type=float, default=0.0)
    
    args = parser.parse_args()
    
    # Get interface from environment or argument
    interface = args.interface or os.getenv("CLIENT_IF")
    if not interface:
        print("ERROR: No interface specified. Set CLIENT_IF environment variable or use --interface")
        sys.exit(1)
    
    # Parse trace
    try:
        trace_points = parse_trace_file(args.trace_file)
    except Exception as e:
        print(f"ERROR: Failed to parse trace file: {e}")
        sys.exit(1)
    
    if not trace_points:
        print("ERROR: Trace file is empty")
        sys.exit(1)
    
    print(f"Loaded {len(trace_points)} trace points")
    print(f"Starting trace replay on {interface}...")
    print("Press Ctrl+C to stop")
    
    start_time = time.time() + args.start_time
    trace_index = 0
    
    try:
        while trace_index < len(trace_points):
            current_time = time.time()
            elapsed_ms = (current_time - start_time) * 1000
            
            # Find the appropriate trace point
            while (trace_index < len(trace_points) - 1 and 
                   trace_points[trace_index + 1]['time_ms'] <= elapsed_ms):
                trace_index += 1
            
            point = trace_points[trace_index]
            
            # Apply configuration
            apply_netem_config(
                interface,
                delay_ms=point['delay_ms'],
                jitter_ms=point.get('jitter_ms', 0),
                loss_pct=point['loss_pct'],
                rate_mbps=point['rate_mbps']
            )
            
            # Calculate sleep time until next point
            if trace_index < len(trace_points) - 1:
                next_time_ms = trace_points[trace_index + 1]['time_ms']
                sleep_ms = next_time_ms - elapsed_ms
                if sleep_ms > 0:
                    time.sleep(sleep_ms / 1000.0)
                trace_index += 1
            else:
                # Last point, keep it applied
                print(f"Trace complete. Final state: delay={point['delay_ms']}ms, loss={point['loss_pct']}%")
                time.sleep(1)
    
    except KeyboardInterrupt:
        print("\nTrace replay interrupted")
        # Reset to passthrough
        apply_netem_config(interface, delay_ms=0, jitter_ms=0, loss_pct=0, rate_mbps=None)
        print("Reset to passthrough configuration")


if __name__ == "__main__":
    main()

