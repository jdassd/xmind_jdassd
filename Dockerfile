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

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./backend/
COPY run.py config.yaml ./

# Copy frontend build artifacts from stage 1
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Data volume for SQLite persistence
RUN mkdir -p /app/data
VOLUME /app/data

# Port configuration via environment variable (default 8080)
ENV MINDMAP_PORT=8080
EXPOSE ${MINDMAP_PORT}

CMD ["python", "run.py"]
