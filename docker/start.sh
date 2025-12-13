#!/bin/bash

# Start Python server in background on port 8001
export PORT=8001
echo "Starting Python backend on port $PORT..."
python server.py &

# Start Nginx in foreground
echo "Starting Nginx..."
nginx -g 'daemon off;'
