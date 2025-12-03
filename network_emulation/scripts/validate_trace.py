#!/usr/bin/env python3
"""
Validate network trace CSV file format and content.
"""

import sys
import csv
import argparse


def validate_trace_file(trace_file):
    """Validate trace file format."""
    errors = []
    warnings = []
    
    try:
        with open(trace_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            if not rows:
                errors.append("Trace file is empty")
                return errors, warnings
            
            # Check required columns
            required_cols = ['time_ms', 'delay_ms', 'loss_pct']
            for col in required_cols:
                if col not in reader.fieldnames:
                    errors.append(f"Missing required column: {col}")
            
            if errors:
                return errors, warnings
            
            # Validate data
            prev_time = -1
            for i, row in enumerate(rows, start=2):
                try:
                    time_ms = int(row['time_ms'])
                    delay_ms = float(row['delay_ms'])
                    loss_pct = float(row['loss_pct'])
                    
                    if time_ms < prev_time:
                        errors.append(f"Row {i}: time_ms must be monotonically increasing")
                    
                    if delay_ms < 0:
                        errors.append(f"Row {i}: delay_ms must be >= 0")
                    
                    if loss_pct < 0 or loss_pct > 100:
                        errors.append(f"Row {i}: loss_pct must be between 0 and 100")
                    
                    if 'rate_mbps' in row and row['rate_mbps']:
                        rate_mbps = float(row['rate_mbps'])
                        if rate_mbps <= 0:
                            errors.append(f"Row {i}: rate_mbps must be > 0")
                    
                    prev_time = time_ms
                    
                except ValueError as e:
                    errors.append(f"Row {i}: Invalid numeric value - {e}")
            
            if len(rows) < 2:
                warnings.append("Trace file has fewer than 2 data points")
            
    except FileNotFoundError:
        errors.append(f"File not found: {trace_file}")
    except Exception as e:
        errors.append(f"Error reading file: {e}")
    
    return errors, warnings


def main():
    parser = argparse.ArgumentParser(description="Validate network trace file")
    parser.add_argument("trace_file", help="Path to CSV trace file")
    
    args = parser.parse_args()
    
    errors, warnings = validate_trace_file(args.trace_file)
    
    if warnings:
        for w in warnings:
            print(f"WARNING: {w}", file=sys.stderr)
    
    if errors:
        print("Validation FAILED:", file=sys.stderr)
        for e in errors:
            print(f"  ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    else:
        print("Validation PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()

