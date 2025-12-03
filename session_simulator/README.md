# Session Simulator

The session simulator orchestrates streaming experiments based on scenario files.

## Scenario Files

Scenarios are YAML files that describe:
- Experiment identifier and description
- Protocol to test (DASH, LL-DASH, WebRTC, MoQ)
- MPD/manifest URL
- Network profile (static or trace-based)
- Experiment duration

## Scenario Schema

See `schema/scenario_schema.json` for the complete schema definition.

### Example Scenario

```yaml
id: "exp_001_basic_dash"
description: "Basic DASH over simple terrestrial profile"
protocol: "dash"
mpd_url: "http://SERVER_PUBLIC_IP:8080/dash/manifest.mpd"
network_profile:
  type: "static"
  file: "../../network_emulation/config/netem_profile_example.yaml"
experiment:
  duration_s: 120
  output_dir: "../../experiments/results/exp_001_basic_dash"
```

## Scenario Runner

The `scripts/scenario_runner.py` script:
1. Loads and validates a scenario file
2. Applies the network profile to the traffic shaper
3. Provides instructions for opening the client player
4. Waits for the experiment duration
5. Exports metrics from MongoDB to JSON

### Usage

```bash
python3 scenario_runner.py scenario.yaml \
  --server-ip 192.168.1.100 \
  --stats-port 8000 \
  --results-dir ../../experiments/results
```

## Network Profile Types

### Static Profile

Uses a YAML file with fixed network conditions:
- `delay_ms`: Base delay
- `jitter_ms`: Delay variation
- `loss_pct`: Packet loss percentage
- `rate_mbps`: Bandwidth limit

### Trace Profile

Uses a CSV file with time-varying conditions:
- `time_ms`: Timestamp in milliseconds
- `delay_ms`: Delay at this time
- `jitter_ms`: Jitter at this time
- `loss_pct`: Loss at this time
- `rate_mbps`: Bandwidth at this time

