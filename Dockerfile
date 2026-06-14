# Stage 1: Build Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .
RUN npm run build

# Stage 2: Backend + FFmpeg + Static Files
FROM python:3.11-slim
LABEL org.opencontainers.image.source=https://github.com/stefexec/Reframe
WORKDIR /app

# Install FFmpeg and AMD VAAPI drivers
RUN apt-get update && \
    apt-get install -y ffmpeg mesa-va-drivers libva-drm2 libva2 fonts-liberation fonts-dejavu fonts-firacode && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Backend Code
COPY backend/ /app/backend/

# Copy Frontend Build
COPY --from=frontend-builder /app/dist /app/frontend

# Directories for uploads, exports and models
RUN mkdir -p /app/uploads /app/exports /app/models

# Expose port
EXPOSE 8080

# Environment variables
ENV DOCKER=1

# Start FastAPI
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
