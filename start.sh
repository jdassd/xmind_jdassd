#!/bin/bash
set -e

# Start Redis in background, persist to /app/data/redis
mkdir -p /app/data/redis
redis-server \
  --daemonize yes \
  --dir /app/data/redis \
  --appendonly yes \
  --save 60 1 \
  --bind 127.0.0.1 \
  --port 6379

# Wait for Redis to be ready
for i in $(seq 1 30); do
  if redis-cli ping >/dev/null 2>&1; then
    echo "Redis is ready"
    break
  fi
  sleep 0.1
done

# Start the Python app (foreground)
exec python run.py
