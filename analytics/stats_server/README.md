# Stats Server

The stats server receives and stores playback metrics from client video players.

## Architecture

Following the MMSys'24 stats-server approach:
- **No Prometheus**: Direct MongoDB storage
- **No Grafana**: Simple REST API
- **Flask-based**: Lightweight Python web server
- **MongoDB storage**: Collections per experiment

## API Endpoints

### POST /api/submit

Receive a metric event from a client.

**Request Body:**
```json
{
    "experiment_id": "exp_001",
    "timestamp": 1234567890.123,
    "event_type": "fragment_loading_completed",
    "protocol": "dash",
    "video_id": "http://...",
    "payload": {
        "url": "...",
        "quality": 2,
        "bitrate": 2000000
    }
}
```

**Response:**
```json
{
    "status": "success"
}
```

### GET /api/health

Health check endpoint.

**Response:**
```json
{
    "status": "healthy",
    "service": "stats_server",
    "mongodb": "connected"
}
```

### GET /api/metrics/<experiment_id>

Retrieve metrics for an experiment.

**Query Parameters:**
- `event_type`: Filter by event type (optional)
- `start_time`: Start timestamp filter (optional)
- `end_time`: End timestamp filter (optional)

**Response:**
```json
{
    "experiment_id": "exp_001",
    "count": 150,
    "metrics": [...]
}
```

## Storage Structure

Metrics are stored in MongoDB collections named `metrics-{experiment_id}`.

Each document contains:
- `experiment_id`: Experiment identifier
- `timestamp`: Unix timestamp in seconds
- `event_type`: Type of event
- `protocol`: Protocol name (e.g., "dash")
- `video_id`: Video/MPD identifier
- `payload`: Event-specific data (JSON)
- `stored_at`: Server-side timestamp

## Configuration

Environment variables:
- `MONGO_HOST`: MongoDB host (default: "mongo")
- `MONGO_PORT`: MongoDB port (default: 27017)
- `MONGO_USERNAME`: MongoDB username (default: "starlink")
- `MONGO_PASSWORD`: MongoDB password (default: "starlink")
- `MONGO_DATABASE`: Database name (default: "testbed")
- `SERVER_HOST`: Server bind address (default: "0.0.0.0")
- `SERVER_PORT`: Server port (default: 8000)

