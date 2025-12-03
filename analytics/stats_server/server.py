"""
Stats Server - Receives and stores playback metrics from clients.

This server follows the MMSys'24 stats-server approach:
- Receives JSON metrics via POST requests
- Stores metrics in MongoDB
- No Prometheus/Grafana dependencies
"""

from flask import Flask
from flask_cors import CORS
from storage import MetricsStorage
from routes import register_routes
import config


def create_app():
    """Create and configure Flask application."""
    app = Flask(__name__)
    
    # Enable CORS for all routes
    CORS(app)
    
    # Initialize storage
    try:
        storage = MetricsStorage()
    except Exception as e:
        print(f"FATAL: Failed to initialize storage: {e}")
        raise
    
    # Register routes
    register_routes(app, storage)
    
    return app, storage


if __name__ == "__main__":
    print("=== Stats Server Starting ===")
    print(f"MongoDB: {config.MONGO_HOST}:{config.MONGO_PORT}")
    print(f"Server: {config.SERVER_HOST}:{config.SERVER_PORT}")
    
    app, storage = create_app()
    
    try:
        app.run(
            host=config.SERVER_HOST,
            port=config.SERVER_PORT,
            debug=False
        )
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        storage.close()

