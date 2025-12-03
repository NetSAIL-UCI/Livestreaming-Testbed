# MongoDB with initialization script
FROM mongo:4.4.22

# Copy initialization script
COPY mongo-init.js /docker-entrypoint-initdb.d/

# The mongo image automatically runs scripts in /docker-entrypoint-initdb.d/
# on first initialization

