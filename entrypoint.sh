#!/bin/bash
set -e

# Initialize MySQL data directory if empty (first run)
if [ ! -d "/var/lib/mysql/mysql" ]; then
    echo "Initializing MySQL data directory..."
    mysqld --initialize-insecure --user=mysql --datadir=/var/lib/mysql
fi

# Start MySQL in background
echo "Starting MySQL..."
mysqld --user=mysql --datadir=/var/lib/mysql &

# Wait for MySQL to be ready
echo "Waiting for MySQL to be ready..."
for i in $(seq 1 30); do
    if mysqladmin ping -h 127.0.0.1 --silent 2>/dev/null; then
        echo "MySQL is ready."
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "MySQL failed to start within 30 seconds."
        exit 1
    fi
    sleep 1
done

# Create database and user if they don't exist (first run)
mysql -h 127.0.0.1 -u root <<-EOSQL
    CREATE DATABASE IF NOT EXISTS mindmap CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    CREATE USER IF NOT EXISTS 'mindmap'@'%' IDENTIFIED BY 'mindmap';
    GRANT ALL PRIVILEGES ON mindmap.* TO 'mindmap'@'%';
    FLUSH PRIVILEGES;
EOSQL

echo "Starting application..."
exec python run.py
