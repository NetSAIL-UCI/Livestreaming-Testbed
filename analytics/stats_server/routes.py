"""
HTTP routes for stats server.
"""

from flask import request, jsonify
from storage import MetricsStorage
import traceback


def register_routes(app, storage):
    """
    Register routes with Flask app.
    
    Args:
        app: Flask application instance
        storage: MetricsStorage instance
    """
    
    @app.route("/api/submit", methods=["POST"])
    def submit_metric():
        """
        Receive and store a metric event from a client.
        
        Expected JSON format:
        {
            "experiment_id": "exp_001",
            "timestamp": 1234567890.123,
            "event_type": "fragment_loading_completed",
            "protocol": "dash",
            "video_id": "http://...",
            "payload": {...}
        }
        """
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({"error": "No JSON data provided"}), 400
            
            # Validate required fields
            required_fields = ["experiment_id", "timestamp", "event_type", "protocol", "payload"]
            for field in required_fields:
                if field not in data:
                    return jsonify({"error": f"Missing required field: {field}"}), 400
            
            # Store metric
            storage.store_metric(
                experiment_id=data["experiment_id"],
                event_type=data["event_type"],
                protocol=data["protocol"],
                video_id=data.get("video_id", "unknown"),
                payload=data["payload"],
                timestamp=data["timestamp"]
            )
            
            return jsonify({"status": "success"}), 200
        
        except Exception as e:
            print(f"ERROR in /api/submit: {e}")
            print(traceback.format_exc())
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/health", methods=["GET"])
    def health_check():
        """Health check endpoint."""
        try:
            # Try to ping MongoDB
            storage.db.command('ping')
            return jsonify({
                "status": "healthy",
                "service": "stats_server",
                "mongodb": "connected"
            }), 200
        except Exception as e:
            return jsonify({
                "status": "unhealthy",
                "service": "stats_server",
                "mongodb": "disconnected",
                "error": str(e)
            }), 503
    
    @app.route("/api/metrics/<experiment_id>", methods=["GET"])
    def get_metrics(experiment_id):
        """
        Retrieve metrics for an experiment.
        
        Query parameters:
        - event_type: Filter by event type
        - start_time: Start timestamp filter
        - end_time: End timestamp filter
        """
        try:
            event_type = request.args.get("event_type")
            start_time = request.args.get("start_time", type=float)
            end_time = request.args.get("end_time", type=float)
            
            metrics = storage.get_metrics(
                experiment_id=experiment_id,
                event_type=event_type,
                start_time=start_time,
                end_time=end_time
            )
            
            # Convert ObjectId to string
            for metric in metrics:
                if "_id" in metric:
                    metric["_id"] = str(metric["_id"])
            
            return jsonify({
                "experiment_id": experiment_id,
                "count": len(metrics),
                "metrics": metrics
            }), 200
        
        except Exception as e:
            print(f"ERROR in /api/metrics: {e}")
            return jsonify({"error": str(e)}), 500

