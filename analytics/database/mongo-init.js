// MongoDB initialization script
// This script runs when MongoDB container is first created

// Switch to testbed database
db = db.getSiblingDB('testbed');

// Create user in testbed database
db.createUser({
  user: 'starlink',
  pwd: 'starlink',
  roles: [
    { role: 'readWrite', db: 'testbed' }
  ]
});

// Create collections (MongoDB creates them automatically on first insert, but we can pre-create)
db.createCollection('metrics');

// Create indexes for better query performance
db.metrics.createIndex({ "experiment_id": 1, "timestamp": 1 });
db.metrics.createIndex({ "event_type": 1 });
db.metrics.createIndex({ "timestamp": 1 });

print("MongoDB initialization complete");

