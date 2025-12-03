# Setup Guide

Quick setup instructions for the testbed.

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- Python 3.10+
- Chrome browser
- Server with public IP accessible from laptop

## Step 1: Clone and Navigate

```bash
cd testbed
```

## Step 2: Prepare DASH Content

Place your DASH content in:
```
protocol_integration/dash/media_server/segments/
```

Required files:
- `manifest.mpd` - DASH manifest
- Media segments (`.m4s`, `.mp4`, etc.)

See `protocol_integration/dash/media_server/segments/README.md` for generating test content.

## Step 3: Start Services

```bash
docker-compose -f docker-compose-emulation.yaml up -d
```

Wait for all containers to be healthy:
```bash
docker-compose -f docker-compose-emulation.yaml ps
```

## Step 4: Verify Services

**Media Server:**
```bash
curl http://localhost:8080/health
# Should return: healthy
```

**Stats Server:**
```bash
curl http://localhost:8000/api/health
# Should return JSON with status: "healthy"
```

**MongoDB:**
```bash
docker exec mongo mongosh --eval "db.adminCommand('ping')"
# Should return: { ok: 1 }
```

## Step 5: Run Your First Experiment

```bash
cd session_simulator/scripts
python3 scenario_runner.py \
  ../scenarios/example_scenario_basic_dash.yaml \
  --server-ip YOUR_SERVER_IP \
  --stats-port 8000
```

Replace `YOUR_SERVER_IP` with your server's public IP address.

## Step 6: Open Client Player

The scenario runner will print a URL. Open it in Chrome:

```
file:///absolute/path/to/testbed/protocol_integration/dash/client_examples/dash_player.html?mpd=http://YOUR_SERVER_IP:8080/dash/manifest.mpd&stats_server=http://YOUR_SERVER_IP:8000&experiment_id=exp_001_basic_dash
```

## Step 7: View Results

After experiment completes, results are in:
```
experiments/results/<run-id>/
├── scenario.yaml
├── stats/
│   └── metrics.json
└── logs/
```

## Troubleshooting

### Containers not starting

```bash
docker-compose -f docker-compose-emulation.yaml logs
```

### Network shaping not working

```bash
# Check traffic_shaper interfaces
docker exec traffic_shaper ip link show

# Check tc rules
docker exec traffic_shaper tc qdisc show
```

### MongoDB connection issues

```bash
# Check MongoDB logs
docker logs mongo

# Test connection from stats_server
docker exec stats_server python3 -c "from storage import MetricsStorage; s = MetricsStorage()"
```

## Next Steps

- Create custom network profiles in `network_emulation/config/`
- Create custom traces in `network_emulation/traces/`
- Create custom scenarios in `session_simulator/scenarios/`
- Run batch experiments with `runner/run_batch.py`

