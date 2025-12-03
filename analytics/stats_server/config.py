"""
Configuration for stats server.
"""

import os

# MongoDB connection
MONGO_HOST = os.getenv("MONGO_HOST", "mongo")
MONGO_PORT = int(os.getenv("MONGO_PORT", "27017"))
MONGO_USERNAME = os.getenv("MONGO_USERNAME", "starlink")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD", "starlink")
MONGO_DATABASE = os.getenv("MONGO_DATABASE", "testbed")

# Server configuration
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))

# MongoDB connection string
# Authenticate against admin database, then use testbed database
MONGO_URI = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DATABASE}?authSource=admin"

