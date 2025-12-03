# DASH Protocol Integration

This module provides DASH (Dynamic Adaptive Streaming over HTTP) support for the testbed.

## Components

### Media Server

Located in `media_server/`:
- **Dockerfile**: NGINX-based container serving DASH content
- **nginx.conf**: NGINX configuration with CORS support for DASH playback
- **segments/**: Directory containing MPD file and media segments

### Client Examples

Located in `client_examples/`:
- **dash_player.html**: HTML5 video player with dash.js integration
- **dash_player.js**: JavaScript with metrics instrumentation

## Usage

### Media Server

The media server runs in a Docker container and serves DASH content on port 8080.

Access the MPD at: `http://SERVER_IP:8080/dash/manifest.mpd`

### Client Player

Open `dash_player.html` in a browser with query parameters:

```
file:///path/to/dash_player.html?mpd=http://SERVER_IP:8080/dash/manifest.mpd&stats_server=http://SERVER_IP:8000&experiment_id=exp_001
```

Parameters:
- `mpd`: URL to the DASH MPD file
- `stats_server`: URL to the stats server (default: http://SERVER_IP:8000)
- `experiment_id`: Experiment identifier for metrics collection

## Metrics Collected

The client automatically sends the following metrics to the stats server:

- `stream_initialized`: When the stream is loaded
- `fragment_loading_started`: When a segment download begins
- `fragment_loading_completed`: When a segment download completes
- `quality_change_rendered`: When bitrate switches occur
- `buffer_level_updated`: Buffer occupancy updates
- `playback_state_changed`: Play/pause state changes
- `rebuffer_event`: When playback stalls
- `playback_error`: Error events
- `periodic_metrics`: Periodic status updates (every 5 seconds)

## Generating DASH Content

See `media_server/segments/README.md` for instructions on generating DASH test content.

