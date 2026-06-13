# Stage 1: Build Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .
RUN npm run build

# Stage 2: Backend + FFmpeg + Static Files
FROM python:3.11-slim
WORKDIR /app

# Install FFmpeg
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Backend Code
COPY backend/ /app/backend/

# Copy Frontend Build
COPY --from=frontend-builder /app/dist /app/frontend

# Directories for uploads and exports
RUN mkdir -p /app/uploads /app/exports

# Expose port
EXPOSE 8080

# Environment variables
ENV DOCKER=1

# Start FastAPI
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
