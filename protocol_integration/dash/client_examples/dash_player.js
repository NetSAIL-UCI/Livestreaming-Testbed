/**
 * DASH Player with Metrics Collection
 * 
 * This script initializes dash.js player and instruments playback events
 * to send metrics to the stats_server.
 */

let dashPlayer = null;
let statsServerUrl = window.STATS_SERVER_URL || 'http://localhost:8000';
let experimentId = window.EXPERIMENT_ID || 'default_experiment';
let lastBufferLevel = 0;
let lastBitrate = 0;
let rebufferCount = 0;
let lastPlaybackState = 'unknown';

/**
 * Send metric event to stats server
 */
function sendMetric(eventType, payload) {
    const metric = {
        experiment_id: experimentId,
        timestamp: Date.now() / 1000.0,  // Unix timestamp in seconds
        event_type: eventType,
        protocol: 'dash',
        video_id: window.currentMpdUrl || 'unknown',
        payload: payload
    };

    fetch(`${statsServerUrl}/api/submit`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(metric)
    }).catch(error => {
        console.error('Failed to send metric:', error);
    });
}

/**
 * Initialize DASH player
 */
function initializeDashPlayer(mpdUrl) {
    if (dashPlayer) {
        dashPlayer.destroy();
    }

    window.currentMpdUrl = mpdUrl;
    const video = document.getElementById('videoPlayer');
    
    updateStatus('Initializing player...');
    logEvent(`Loading MPD: ${mpdUrl}`);

    // Create dash.js player instance
    dashPlayer = dashjs.MediaPlayer().create();
    dashPlayer.initialize(video, mpdUrl, true);

    // Store globally for access
    window.dashPlayer = dashPlayer;

    // === Event Handlers ===

    // Player ready
    dashPlayer.on(dashjs.MediaPlayer.events.STREAM_INITIALIZED, function() {
        updateStatus('Stream initialized');
        logEvent('Stream initialized');
        
        sendMetric('stream_initialized', {
            mpd_url: mpdUrl
        });
    });

    // Fragment loading completed
    dashPlayer.on(dashjs.MediaPlayer.events.FRAGMENT_LOADING_COMPLETED, function(e) {
        if (e && e.request) {
            const request = e.request;
            const quality = dashPlayer.getQualityFor('video');
            
            sendMetric('fragment_loading_completed', {
                type: request.type,
                url: request.url,
                quality: quality,
                media_type: request.mediaType,
                start_time: request.startTime,
                duration: request.duration
            });
        }
    });

    // Fragment loading started
    dashPlayer.on(dashjs.MediaPlayer.events.FRAGMENT_LOADING_STARTED, function(e) {
        if (e && e.request) {
            sendMetric('fragment_loading_started', {
                type: e.request.type,
                url: e.request.url,
                media_type: e.request.mediaType
            });
        }
    });

    // Quality change rendered
    dashPlayer.on(dashjs.MediaPlayer.events.QUALITY_CHANGE_RENDERED, function(e) {
        if (e && e.quality !== undefined) {
            const bitrate = dashPlayer.getBitrateInfoListFor('video')[e.quality].bitrate;
            lastBitrate = bitrate;
            
            updateMetric('currentBitrate', (bitrate / 1000).toFixed(0) + ' kbps');
            logEvent(`Quality change: ${bitrate} bps`);
            
            sendMetric('quality_change_rendered', {
                old_quality: e.oldQuality,
                new_quality: e.quality,
                bitrate: bitrate
            });
        }
    });

    // Buffer level updated
    dashPlayer.on(dashjs.MediaPlayer.events.BUFFER_LEVEL_UPDATED, function(e) {
        if (e && e.bufferLevel !== undefined) {
            const bufferLevel = e.bufferLevel;
            lastBufferLevel = bufferLevel;
            
            updateMetric('bufferLevel', bufferLevel.toFixed(2) + 's');
            
            sendMetric('buffer_level_updated', {
                buffer_level: bufferLevel,
                media_type: e.mediaType
            });
        }
    });

    // Playback state changed
    dashPlayer.on(dashjs.MediaPlayer.events.PLAYBACK_STATE_CHANGED, function(e) {
        if (e && e.state !== undefined) {
            const newState = e.state;
            
            if (lastPlaybackState === 'playing' && newState === 'paused') {
                logEvent('Playback paused');
            } else if (lastPlaybackState === 'paused' && newState === 'playing') {
                logEvent('Playback resumed');
            }
            
            lastPlaybackState = newState;
            
            sendMetric('playback_state_changed', {
                old_state: lastPlaybackState,
                new_state: newState
            });
        }
    });

    // Playback error
    dashPlayer.on(dashjs.MediaPlayer.events.ERROR, function(e) {
        if (e && e.error) {
            logEvent(`ERROR: ${e.error.message || 'Unknown error'}`);
            
            sendMetric('playback_error', {
                error_code: e.error.code,
                error_message: e.error.message,
                error_data: e.error.data
            });
        }
    });

    // Rebuffer events (stall detection)
    dashPlayer.on(dashjs.MediaPlayer.events.PLAYBACK_STALLED, function() {
        rebufferCount++;
        logEvent(`Rebuffer detected (#${rebufferCount})`);
        
        sendMetric('rebuffer_event', {
            rebuffer_count: rebufferCount,
            buffer_level: lastBufferLevel,
            current_bitrate: lastBitrate
        });
    });

    dashPlayer.on(dashjs.MediaPlayer.events.PLAYBACK_STARTED, function() {
        updateStatus('Playing');
        logEvent('Playback started');
        
        sendMetric('playback_started', {
            mpd_url: mpdUrl
        });
    });

    dashPlayer.on(dashjs.MediaPlayer.events.PLAYBACK_ENDED, function() {
        updateStatus('Playback ended');
        logEvent('Playback ended');
        
        sendMetric('playback_ended', {
            total_rebuffers: rebufferCount
        });
    });

    // Periodic metrics collection
    setInterval(function() {
        if (dashPlayer && video) {
            const playbackRate = video.playbackRate;
            const currentTime = video.currentTime;
            const duration = video.duration;
            const droppedFrames = video.getVideoPlaybackQuality ? 
                video.getVideoPlaybackQuality().droppedVideoFrames : 0;
            
            updateMetric('playbackRate', playbackRate.toFixed(2) + 'x');
            updateMetric('droppedFrames', droppedFrames);
            
            sendMetric('periodic_metrics', {
                current_time: currentTime,
                duration: duration,
                playback_rate: playbackRate,
                dropped_frames: droppedFrames,
                buffer_level: lastBufferLevel,
                current_bitrate: lastBitrate
            });
        }
    }, 5000);  // Every 5 seconds

    updateStatus('Player initialized');
}

/**
 * Update metric display
 */
function updateMetric(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value;
    }
}

// Export for use in HTML
window.initializeDashPlayer = initializeDashPlayer;

