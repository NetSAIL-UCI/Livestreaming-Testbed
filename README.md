# Livestreaming Testbed

A modular testbed for comparing livestreaming protocols (DASH, LL-DASH, WebRTC, MoQ) under various network conditions.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Physical & Logical Topology](#physical--logical-topology)
- [Repository Structure](#repository-structure)
- [Quick Start](#quick-start)
- [Module Details](#module-details)
- [Running Experiments](#running-experiments)
- [Extending to Other Protocols](#extending-to-other-protocols)
- [Phase 2: Real Starlink](#phase-2-real-starlink)
- [Troubleshooting](#troubleshooting)

## Overview

This testbed implements a four-module architecture for streaming protocol evaluation:

1. **Network Emulation Module**: Uses `tc/netem` to emulate terrestrial networks with configurable delay, jitter, loss, and bandwidth limits
2. **Protocol Integration Module**: Currently implements DASH fully; placeholders for LL-DASH, WebRTC, and MoQ
3. **Streaming Session Simulator**: Scenario-based experiment runner that orchestrates network conditions and playback
4. **Performance & Analytics Module**: Stats server (MMSys'24 approach) with MongoDB storage - **no Prometheus/Grafana**

## Architecture

### Design Goals

- **Modular**: Each module is independent and can be extended
- **Containerized**: All server components run in Docker containers
- **Client-side playback**: Video players run in browser on laptop (not in containers)
- **Metrics collection**: Stats-server approach following MMSys'24 artifact
- **Network shaping**: All traffic shaping happens on server in dedicated container

### Module Interaction

```
┌─────────────┐
│   Laptop    │  (Browser with DASH player)
│   Client    │
└──────┬──────┘
       │ HTTP GET /dash/manifest.mpd
       │
       v
┌─────────────────────────────────────┐
│         Server (Docker)              │
│                                     │
│  ┌──────────────────────────────┐  │
│  │  traffic_shaper container    │  │
│  │  (tc/netem)                   │  │
│  └───────────┬──────────────────┘  │
│              │                       │
│              v                       │
│  ┌──────────────────────────────┐  │
│  │  dash_media_server (NGINX)   │  │
│  └──────────────────────────────┘  │
│                                     │
│  ┌──────────────────────────────┐  │
│  │  stats_server (Flask)        │  │
│  └───────────┬──────────────────┘  │
│              │                       │
│              v                       │
│  ┌──────────────────────────────┐  │
│  │  mongo (MongoDB)             │  │
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘
```

## Physical & Logical Topology

### Physical Topology

- **Laptop**: Runs client video players in Chrome browser
- **Server**: Runs all Docker containers (traffic shaper, media server, stats server, MongoDB)
- **Connection**: Laptop connects to server over LAN/WiFi (Phase 1: terrestrial)

### Logical Data Path

```
Laptop Browser (DASH client)
        |
        | HTTP GET /dash/manifest.mpd
        |
        v
(Server Public IP:8080)
        |
        v
[Docker Host] -- port mapping
        |
        v
[traffic_shaper container] -- applies tc/netem on server_side_net
        |
        v
[dash_media_server container] (on server_side_net)
```

**Note**: In the current setup, the traffic_shaper shapes traffic on the `server_side_net` interface, which affects communication between the traffic_shaper and media_server containers. The client connects through the host's port mapping (8080), and network conditions are applied to the server-side network path. For Phase 2 with real Starlink, the traffic_shaper will be positioned to shape all incoming/outgoing traffic.

### Metrics Path

```
Laptop Browser (DASH client)
        |
        | POST /api/submit (JSON metrics)
        |
        v
(Server Public IP:8000)
        |
        v
[stats_server container]
        |
        v
[mongo container]
```

## Repository Structure

```
testbed/
├── README.md                          # This file
├── docker-compose-emulation.yaml      # Docker Compose configuration
│
├── network_emulation/                 # Module 1: Network Emulation
│   ├── Dockerfile
│   ├── entrypoint.sh
│   ├── config/
│   │   └── netem_profile_example.yaml
│   ├── traces/
│   │   └── example_terrestrial_trace.csv
│   └── scripts/
│       ├── apply_static_profile.py
│       ├── replay_trace.py
│       └── validate_trace.py
│
├── protocol_integration/              # Module 2: Protocol Integration
│   ├── dash/
│   │   ├── media_server/
│   │   │   ├── Dockerfile
│   │   │   ├── nginx.conf
│   │   │   └── segments/
│   │   └── client_examples/
│   │       ├── dash_player.html
│   │       └── dash_player.js
│   ├── lldash/                        # Placeholder
│   ├── webrtc/                        # Placeholder
│   └── moq/                           # Placeholder
│
├── session_simulator/                  # Module 3: Session Simulator
│   ├── scenarios/
│   │   ├── example_scenario_basic_dash.yaml
│   │   └── example_scenario_trace_dash.yaml
│   ├── schema/
│   │   └── scenario_schema.json
│   └── scripts/
│       └── scenario_runner.py
│
├── analytics/                          # Module 4: Analytics
│   ├── stats_server/
│   │   ├── Dockerfile
│   │   ├── server.py
│   │   ├── routes.py
│   │   ├── storage.py
│   │   ├── config.py
│   │   └── requirements.txt
│   └── database/
│       ├── Dockerfile
│       └── mongo-init.js
│
├── runner/                            # Experiment Runner
│   ├── Dockerfile
│   ├── run_experiment.py
│   ├── run_batch.py
│   └── utils/
│       ├── docker_utils.py
│       ├── timestamp_utils.py
│       └── logging_utils.py
│
└── experiments/
    ├── configs/
    │   ├── exp_001_basic_terrestrial_dash.yaml
    │   └── exp_002_trace_terrestrial_dash.yaml
    └── results/
        └── .gitignore
```

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Python 3.10+ (for runner scripts)
- Chrome browser (for client playback)
- Server with public IP accessible from laptop

### 1. Start Services

```bash
cd testbed
docker-compose -f docker-compose-emulation.yaml up -d
```

Verify containers are running:
```bash
docker-compose -f docker-compose-emulation.yaml ps
```

### 2. Prepare DASH Content

Place your DASH content in `protocol_integration/dash/media_server/segments/`:
- `manifest.mpd` - DASH manifest file
- Media segments (`.m4s` files, etc.)

See `protocol_integration/dash/media_server/segments/README.md` for details on generating DASH content.

### 3. Run an Experiment

**Option A: Using scenario runner directly**

```bash
cd session_simulator/scripts
python3 scenario_runner.py \
  ../scenarios/example_scenario_basic_dash.yaml \
  --server-ip YOUR_SERVER_IP \
  --stats-port 8000
```

**Option B: Using main runner**

```bash
cd runner
python3 run_experiment.py \
  ../experiments/configs/exp_001_basic_terrestrial_dash.yaml \
  --server-ip YOUR_SERVER_IP
```

### 4. Open Client Player

The scenario runner will print instructions. Open the DASH player in your browser:

```
file:///path/to/testbed/protocol_integration/dash/client_examples/dash_player.html?mpd=http://YOUR_SERVER_IP:8080/dash/manifest.mpd&stats_server=http://YOUR_SERVER_IP:8000&experiment_id=exp_001_basic_dash
```

### 5. View Results

After the experiment completes, results are saved to:
```
experiments/results/<run-id>/
├── scenario.yaml          # Copy of scenario file
├── stats/
│   └── metrics.json       # Exported metrics from MongoDB
└── logs/                  # Experiment logs
```

## Module Details

### Network Emulation Module

The traffic shaper container applies network conditions using `tc/netem`.

**Static Profile** (YAML):
```yaml
delay_ms: 50
jitter_ms: 10
loss_pct: 0.5
rate_mbps: 10
```

**Trace Profile** (CSV):
```csv
time_ms,delay_ms,jitter_ms,loss_pct,rate_mbps
0,50,5,0,10
1000,75,10,0.1,8
```

**Manual Application:**
```bash
docker exec traffic_shaper python3 /app/scripts/apply_static_profile.py /app/config/netem_profile_example.yaml
```

### Protocol Integration Module

#### DASH (Fully Implemented)

**Media Server:**
- NGINX serving DASH content on port 8080
- CORS enabled for browser playback
- Byte-range request support

**Client:**
- HTML5 player with dash.js
- Automatic metrics collection
- Real-time bitrate and buffer display

**Access:**
- MPD: `http://SERVER_IP:8080/dash/manifest.mpd`
- Health: `http://SERVER_IP:8080/health`

#### LL-DASH, WebRTC, MoQ (Placeholders)

These protocols have placeholder directories. Implementation planned for Phase 2.

### Streaming Session Simulator

Scenarios are YAML files describing experiments:

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

The scenario runner:
1. Loads and validates scenario
2. Applies network profile to traffic shaper
3. Provides client instructions
4. Waits for experiment duration
5. Exports metrics from MongoDB

### Performance & Analytics Module

**Stats Server:**
- Flask-based REST API
- Receives JSON metrics from clients
- Stores in MongoDB collections per experiment
- **No Prometheus/Grafana** (MMSys'24 approach)

**Endpoints:**
- `POST /api/submit` - Submit metric event
- `GET /api/health` - Health check
- `GET /api/metrics/<experiment_id>` - Retrieve metrics

**Metrics Collected:**
- `stream_initialized`
- `fragment_loading_started`
- `fragment_loading_completed`
- `quality_change_rendered`
- `buffer_level_updated`
- `playback_state_changed`
- `rebuffer_event`
- `playback_error`
- `periodic_metrics`

## Running Experiments

### Single Experiment

```bash
cd runner
python3 run_experiment.py \
  ../experiments/configs/exp_001_basic_terrestrial_dash.yaml \
  --server-ip 192.168.1.100
```

### Batch Experiments

```bash
cd runner
python3 run_batch.py \
  ../session_simulator/scenarios \
  --server-ip 192.168.1.100 \
  --pattern "*.yaml"
```

### Manual Network Profile Application

```bash
# Static profile
docker exec traffic_shaper python3 /app/scripts/apply_static_profile.py /app/config/netem_profile_example.yaml

# Trace replay
docker exec traffic_shaper python3 /app/scripts/replay_trace.py /app/traces/example_terrestrial_trace.csv
```

## Extending to Other Protocols

### Adding LL-DASH

1. Create `protocol_integration/lldash/media_server/` with LL-DASH server
2. Create `protocol_integration/lldash/client_examples/` with LL-DASH player
3. Update scenario schema to support `lldash` protocol
4. Add service to `docker-compose-emulation.yaml`

### Adding WebRTC

1. Create `protocol_integration/webrtc/` with WebRTC signaling server
2. Create WebRTC client example
3. Update scenario schema
4. Add service to docker-compose

### Adding MoQ

1. Create `protocol_integration/moq/` with MoQ server
2. Create MoQ client example
3. Update scenario schema
4. Add service to docker-compose

**Client Integration:**
- Follow the DASH client pattern
- Send metrics to stats_server at `/api/submit`
- Include `experiment_id`, `protocol`, `event_type`, `payload`

## Phase 2: Real Starlink

For Phase 2 with real Starlink connectivity:

1. **Network Module**: Replace `tc/netem` with real Starlink interface monitoring
2. **Trace Collection**: Collect real Starlink network traces
3. **Trace Replay**: Replay collected traces using the existing trace replay mechanism
4. **Physical Setup**: Connect server to Starlink terminal

The existing architecture supports this transition - only the network emulation source changes.

## Troubleshooting

### Docker Network Issues

**Problem**: Client cannot reach media server

**Solution**:
1. Check container networks: `docker network ls`
2. Verify traffic_shaper is on both networks: `docker inspect traffic_shaper`
3. Check port mappings: `docker-compose ps`
4. Verify firewall rules on server

### tc/netem Not Working

**Problem**: Network shaping not applying

**Solution**:
1. Verify container is privileged: `docker inspect traffic_shaper | grep Privileged`
2. Check interface names: `docker exec traffic_shaper ip link show`
3. Verify tc rules: `docker exec traffic_shaper tc qdisc show`
4. Check container logs: `docker logs traffic_shaper`

### MongoDB Connection Issues

**Problem**: Stats server cannot connect to MongoDB

**Solution**:
1. Verify MongoDB is running: `docker ps | grep mongo`
2. Check MongoDB logs: `docker logs mongo`
3. Verify connection string in stats_server environment variables
4. Test connection: `docker exec stats_server python3 -c "from storage import MetricsStorage; s = MetricsStorage()"`

### Client Metrics Not Appearing

**Problem**: Metrics not being stored in MongoDB

**Solution**:
1. Check browser console for errors
2. Verify stats_server URL is correct in client
3. Check stats_server logs: `docker logs stats_server`
4. Test stats_server health: `curl http://SERVER_IP:8000/api/health`
5. Verify CORS is enabled in stats_server

### DASH Playback Issues

**Problem**: Video not playing in browser

**Solution**:
1. Verify MPD is accessible: `curl http://SERVER_IP:8080/dash/manifest.mpd`
2. Check NGINX logs: `docker logs dash_media_server`
3. Verify CORS headers in nginx.conf
4. Check browser console for errors
5. Verify dash.js is loading: Check Network tab in browser DevTools

### Scenario Runner Issues

**Problem**: Scenario runner fails

**Solution**:
1. Validate scenario YAML syntax
2. Check file paths in scenario (use relative paths)
3. Verify containers are running: `docker-compose ps`
4. Check scenario runner logs
5. Verify network profile files exist

## Additional Resources

- **Network Emulation**: See `network_emulation/README.md`
- **DASH Integration**: See `protocol_integration/dash/README.md`
- **Stats Server**: See `analytics/stats_server/README.md`
- **Session Simulator**: See `session_simulator/README.md`
- **Runner**: See `runner/README.md`

## License

[Add your license information here]

## Contact

[Add contact information here]
