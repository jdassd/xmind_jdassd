#!/bin/bash
set -e

echo "=== Entrypoint starting ==="

# Initialize MariaDB data directory if empty (first run)
if [ ! -d "/var/lib/mysql/mysql" ]; then
    echo "Initializing MariaDB data directory..."
    mysql_install_db --user=mysql --datadir=/var/lib/mysql
    echo "MariaDB data directory initialized."
fi

# Ensure correct ownership (in case volume was mounted)
chown -R mysql:mysql /var/lib/mysql /var/run/mysqld

# Start MariaDB in background
echo "Starting MariaDB..."
mysqld_safe --user=mysql --datadir=/var/lib/mysql &

# Wait for MariaDB to be ready (use socket, not TCP)
echo "Waiting for MariaDB to be ready..."
for i in $(seq 1 30); do
    if mysqladmin ping --silent 2>/dev/null; then
        echo "MariaDB is ready."
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "ERROR: MariaDB failed to start within 30 seconds."
        echo "=== MariaDB error log ==="
        cat /var/log/mysql/error.log 2>/dev/null || true
        exit 1
    fi
    sleep 1
done

# Create database and user if they don't exist (first run)
echo "Setting up database and user..."
mysql -u root <<-EOSQL
    CREATE DATABASE IF NOT EXISTS mindmap CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    CREATE USER IF NOT EXISTS 'mindmap'@'127.0.0.1' IDENTIFIED BY 'mindmap';
    CREATE USER IF NOT EXISTS 'mindmap'@'localhost' IDENTIFIED BY 'mindmap';
    GRANT ALL PRIVILEGES ON mindmap.* TO 'mindmap'@'127.0.0.1';
    GRANT ALL PRIVILEGES ON mindmap.* TO 'mindmap'@'localhost';
    FLUSH PRIVILEGES;
EOSQL
echo "Database setup done."

echo "Starting application..."
exec python run.py
