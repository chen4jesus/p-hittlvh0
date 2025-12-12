#!/bin/bash

# Configuration
IMAGE_NAME="churchsite"
CONTAINER_NAME="churchsite_server"
PORT=80
DATA_DIR="./church_data"

echo "Deploying Church Website..."

# 1. Stop and remove existing container if it exists
if [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
    echo "Stopping existing container..."
    docker stop $CONTAINER_NAME
    echo "Removing existing container..."
    docker rm $CONTAINER_NAME
fi

# 2. Build the Docker image
echo "Building Docker image..."
docker build -t $IMAGE_NAME .

# 3. Create data directory for persistence
mkdir -p $DATA_DIR

# 4. Run the container
echo "Starting updated container..."
# -d: Run in background
# -p: Map host port 80 to container port 8000
# -v: Mount local data directory to /app/data in container
# -e: Set DB_FILE env var to use the mounted volume
# --restart: Always restart if it crashes
docker run -d \
    --name $CONTAINER_NAME \
    -p $PORT:8000 \
    -v "$(pwd)/$DATA_DIR:/app/data" \
    -e DB_FILE="/app/data/contacts.db" \
    --restart unless-stopped \
    $IMAGE_NAME

echo "Deployment complete!"
echo "Site is running at http://localhost:$PORT"
echo "Database is persisted in $(pwd)/$DATA_DIR/contacts.db"
