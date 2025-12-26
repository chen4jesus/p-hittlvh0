FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Caddy from official image
COPY --from=caddy:2-alpine /usr/bin/caddy /usr/bin/caddy

# Copy application and config
COPY . .
COPY Caddyfile /etc/caddy/Caddyfile

# Prepare startup script
RUN chmod +x start.sh

# Expose ports
EXPOSE 80 443 8000

# Start both services
CMD ["./start.sh"]
