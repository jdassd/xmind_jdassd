# -- Stage 1: Build frontend --
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# -- Stage 2: Production image --
FROM python:3.11-slim
WORKDIR /app

# Install MariaDB (Debian's default mysql-server is MariaDB)
RUN apt-get update && \
    apt-get install -y --no-install-recommends mariadb-server mariadb-client && \
    rm -rf /var/lib/apt/lists/* && \
    mkdir -p /var/lib/mysql /var/run/mysqld /var/log/mysql && \
    chown -R mysql:mysql /var/lib/mysql /var/run/mysqld /var/log/mysql

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./backend/
COPY run.py config.yaml ./

# Copy frontend build artifacts from stage 1
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Copy entrypoint script
COPY entrypoint.sh ./
RUN chmod +x entrypoint.sh

# MySQL data volume for persistence
VOLUME /var/lib/mysql

# Port configuration
ENV MINDMAP_PORT=8080
EXPOSE ${MINDMAP_PORT}

CMD ["./entrypoint.sh"]
