# Network Emulation Module

This module provides network condition emulation using `tc/netem` inside a dedicated Docker container.

## Overview

The traffic shaper container sits between the client (laptop) and the media server, applying network conditions such as:
- Delay (latency)
- Jitter (delay variation)
- Packet loss
- Bandwidth limits

## Components

- **Dockerfile**: Container image with iproute2, tc, Python3
- **entrypoint.sh**: Detects interfaces and initializes the shaper
- **scripts/apply_static_profile.py**: Applies static network conditions from YAML
- **scripts/replay_trace.py**: Replays time-varying network traces from CSV
- **scripts/validate_trace.py**: Validates trace file format

## Usage

### Static Profile

```bash
# Inside the traffic_shaper container
python3 /app/scripts/apply_static_profile.py /path/to/profile.yaml
```

### Trace Replay

```bash
# Inside the traffic_shaper container
python3 /app/scripts/replay_trace.py /path/to/trace.csv
```

## Configuration Files

- **config/netem_profile_example.yaml**: Example static profile
- **traces/example_terrestrial_trace.csv**: Example time-varying trace

## Interface Detection

The container automatically detects the first two non-loopback network interfaces:
- `CLIENT_IF`: Interface facing the client (laptop)
- `SERVER_IF`: Interface facing the server (media server)

These are exported as environment variables for use by scripts.

