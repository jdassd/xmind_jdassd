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

# Install MySQL server
RUN apt-get update && \
    apt-get install -y --no-install-recommends mysql-server mysql-client && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /var/lib/mysql && \
    mkdir -p /var/lib/mysql /var/run/mysqld && \
    chown -R mysql:mysql /var/lib/mysql /var/run/mysqld

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
