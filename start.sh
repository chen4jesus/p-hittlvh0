#!/bin/sh

# Start Gunicorn in the background
echo "Starting Gunicorn..."
gunicorn --bind 0.0.0.0:8000 wsgi:app &

# Start Caddy in the foreground
echo "Starting Caddy..."
exec caddy run --config /etc/caddy/Caddyfile --adapter caddyfile
