#!/usr/bin/env python3
"""
Apply static network profile using tc/netem.

Reads a YAML configuration file and applies network conditions
to the traffic shaper interfaces.
"""

import os
import sys
import yaml
import subprocess
import argparse


def run_cmd(cmd, check=True):
    """Run a shell command and return the result."""
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True, check=check
    )
    return result.stdout.strip()


def apply_netem_config(interface, delay_ms=0, jitter_ms=0, loss_pct=0, rate_mbps=None):
    """
    Apply netem configuration to an interface.
    
    Args:
        interface: Network interface name
        delay_ms: Base delay in milliseconds
        jitter_ms: Jitter (delay variation) in milliseconds
        loss_pct: Packet loss percentage (0-100)
        rate_mbps: Rate limit in Mbps (optional)
    """
    print(f"Applying netem config to {interface}:")
    print(f"  Delay: {delay_ms}ms")
    print(f"  Jitter: {jitter_ms}ms")
    print(f"  Loss: {loss_pct}%")
    if rate_mbps:
        print(f"  Rate: {rate_mbps}Mbps")
    
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
        # Use prio qdisc to allow filtering
        run_cmd(f"tc qdisc add dev {interface} root handle 1: prio")
        run_cmd(f"tc qdisc add dev {interface} parent 1:1 handle 2: netem {netem_str}")
        run_cmd(f"tc filter add dev {interface} protocol ip parent 1:0 prio 1 u32 match ip dst 0.0.0.0/0 flowid 1:1")
    else:
        # Passthrough (no shaping)
        run_cmd(f"tc qdisc add dev {interface} root handle 1: prio")
        run_cmd(f"tc qdisc add dev {interface} parent 1:1 handle 2: netem delay 0ms")
        run_cmd(f"tc filter add dev {interface} protocol ip parent 1:0 prio 1 u32 match ip dst 0.0.0.0/0 flowid 1:1")
    
    print(f"✓ Configuration applied to {interface}")


def main():
    parser = argparse.ArgumentParser(description="Apply static network profile")
    parser.add_argument("profile_file", help="Path to YAML profile file")
    parser.add_argument("--interface", help="Interface to apply to (default: CLIENT_IF)", default=None)
    
    args = parser.parse_args()
    
    # Get interface from environment or argument
    interface = args.interface or os.getenv("CLIENT_IF")
    if not interface:
        print("ERROR: No interface specified. Set CLIENT_IF environment variable or use --interface")
        sys.exit(1)
    
    # Read profile
    try:
        with open(args.profile_file, 'r') as f:
            profile = yaml.safe_load(f)
    except Exception as e:
        print(f"ERROR: Failed to read profile file: {e}")
        sys.exit(1)
    
    # Extract parameters
    delay_ms = profile.get('delay_ms', 0)
    jitter_ms = profile.get('jitter_ms', 0)
    loss_pct = profile.get('loss_pct', 0)
    rate_mbps = profile.get('rate_mbps', None)
    
    # Apply configuration
    apply_netem_config(interface, delay_ms, jitter_ms, loss_pct, rate_mbps)
    
    print("✓ Static profile applied successfully")


if __name__ == "__main__":
    main()

