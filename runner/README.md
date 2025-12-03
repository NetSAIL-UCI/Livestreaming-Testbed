# Runner Module

The runner module provides scripts for executing streaming experiments.

## Scripts

### run_experiment.py

Runs a single experiment scenario.

**Usage:**
```bash
python3 run_experiment.py scenario.yaml \
  --server-ip 192.168.1.100 \
  --stats-port 8000
```

**Arguments:**
- `scenario_file`: Path to scenario YAML file
- `--server-ip`: Public IP address of the server (required)
- `--stats-port`: Stats server port (default: 8000)
- `--results-dir`: Base results directory (default: ../../experiments/results)
- `--compose-file`: Docker Compose file (default: ../../docker-compose-emulation.yaml)

### run_batch.py

Runs multiple scenarios sequentially.

**Usage:**
```bash
python3 run_batch.py ../../session_simulator/scenarios \
  --server-ip 192.168.1.100 \
  --pattern "*.yaml"
```

**Arguments:**
- `scenario_dir`: Directory containing scenario files
- `--server-ip`: Public IP address of the server (required)
- `--stats-port`: Stats server port (default: 8000)
- `--results-dir`: Base results directory
- `--pattern`: File pattern to match (default: *.yaml)
- `--stop-on-error`: Stop batch on first error

## Utilities

The `utils/` directory contains helper modules:
- `docker_utils.py`: Docker container management
- `timestamp_utils.py`: Timestamp generation and parsing
- `logging_utils.py`: Logging configuration

## Prerequisites

Before running experiments:
1. Start all containers with `docker-compose up -d`
2. Ensure containers are healthy
3. Have scenario files ready
4. Know the server's public IP address

