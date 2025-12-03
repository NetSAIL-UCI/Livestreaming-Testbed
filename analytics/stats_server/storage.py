"""
MongoDB storage interface for metrics.
"""

from pymongo import MongoClient
from datetime import datetime
import config


class MetricsStorage:
    """Wrapper around MongoDB for storing metrics."""
    
    def __init__(self):
        """Initialize MongoDB connection."""
        try:
            self.client = MongoClient(config.MONGO_URI)
            self.db = self.client[config.MONGO_DATABASE]
            print(f"Connected to MongoDB at {config.MONGO_HOST}:{config.MONGO_PORT}")
        except Exception as e:
            print(f"ERROR: Failed to connect to MongoDB: {e}")
            raise
    
    def store_metric(self, experiment_id, event_type, protocol, video_id, payload, timestamp):
        """
        Store a metric event in MongoDB.
        
        Args:
            experiment_id: Experiment identifier
            event_type: Type of event (e.g., 'fragment_loading_completed')
            protocol: Protocol name (e.g., 'dash')
            video_id: Video/MPD identifier
            payload: Event payload (dict)
            timestamp: Unix timestamp in seconds
        """
        collection_name = f"metrics-{experiment_id}"
        collection = self.db[collection_name]
        
        document = {
            "experiment_id": experiment_id,
            "timestamp": timestamp,
            "event_type": event_type,
            "protocol": protocol,
            "video_id": video_id,
            "payload": payload,
            "stored_at": datetime.utcnow()
        }
        
        try:
            result = collection.insert_one(document)
            return result.inserted_id
        except Exception as e:
            print(f"ERROR: Failed to store metric: {e}")
            raise
    
    def get_metrics(self, experiment_id, event_type=None, start_time=None, end_time=None):
        """
        Retrieve metrics for an experiment.
        
        Args:
            experiment_id: Experiment identifier
            event_type: Optional filter by event type
            start_time: Optional start timestamp filter
            end_time: Optional end timestamp filter
        
        Returns:
            List of metric documents
        """
        collection_name = f"metrics-{experiment_id}"
        collection = self.db[collection_name]
        
        query = {}
        if event_type:
            query["event_type"] = event_type
        if start_time:
            query["timestamp"] = {"$gte": start_time}
        if end_time:
            if "timestamp" in query:
                query["timestamp"]["$lte"] = end_time
            else:
                query["timestamp"] = {"$lte": end_time}
        
        return list(collection.find(query).sort("timestamp", 1))
    
    def export_to_json(self, experiment_id, output_file):
        """
        Export all metrics for an experiment to a JSON file.
        
        Args:
            experiment_id: Experiment identifier
            output_file: Path to output JSON file
        """
        import json
        metrics = self.get_metrics(experiment_id)
        
        # Convert ObjectId to string for JSON serialization
        for metric in metrics:
            if "_id" in metric:
                metric["_id"] = str(metric["_id"])
        
        with open(output_file, 'w') as f:
            json.dump(metrics, f, indent=2, default=str)
        
        return len(metrics)
    
    def close(self):
        """Close MongoDB connection."""
        self.client.close()

