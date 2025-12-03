FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    docker.io \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    pyyaml \
    docker

# Copy runner scripts
COPY . .

RUN chmod +x *.py

# Default command
CMD ["python", "run_experiment.py"]

