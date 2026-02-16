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

# Install Redis server
RUN apt-get update && apt-get install -y --no-install-recommends redis-server redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./backend/
COPY run.py config.yaml ./

# Copy startup script
COPY start.sh ./
RUN chmod +x start.sh

# Copy frontend build artifacts from stage 1
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Data volume for SQLite + Redis persistence
RUN mkdir -p /app/data
VOLUME /app/data

# Port configuration via environment variable (default 8080)
ENV MINDMAP_PORT=8080
EXPOSE ${MINDMAP_PORT}

CMD ["./start.sh"]
