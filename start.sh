#!/bin/sh
set -e

# Ensure Redis data directory exists and is writable
mkdir -p /app/data/redis
chmod 777 /app/data/redis

# Start Redis in background with persistence to /app/data/redis
redis-server \
  --daemonize yes \
  --dir /app/data/redis \
  --appendonly yes \
  --save 60 1 \
  --bind 127.0.0.1 \
  --port 6379 \
  --loglevel warning \
  --protected-mode no

# Wait until Redis is actually accepting connections
echo "Waiting for Redis..."
i=0
while [ $i -lt 50 ]; do
  if redis-cli -h 127.0.0.1 ping 2>/dev/null | grep -q PONG; then
    echo "Redis is ready"
    break
  fi
  i=$((i + 1))
  sleep 0.2
done

if ! redis-cli -h 127.0.0.1 ping 2>/dev/null | grep -q PONG; then
  echo "ERROR: Redis failed to start, check logs:"
  cat /app/data/redis/*.log 2>/dev/null || true
  echo "Trying to start Redis without persistence..."
  redis-server --daemonize yes --bind 127.0.0.1 --port 6379 --protected-mode no
  sleep 1
fi

# Start the Python app (foreground, replaces shell)
exec python run.py
