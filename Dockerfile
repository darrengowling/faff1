# Multi-stage Docker build for UCL Auction
FROM node:18-alpine AS frontend-builder

# Build frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/yarn.lock ./
RUN yarn install --frozen-lockfile
COPY frontend/ ./
RUN yarn build

# Python backend stage
FROM python:3.11-slim AS backend

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./backend/

# Copy built frontend
COPY --from=frontend-builder /app/frontend/build ./frontend/build

# Copy seed data and scripts
COPY seed_data/ ./seed_data/
COPY seed_script.py ./
COPY run_seed.sh ./

# Create logs directory
RUN mkdir -p /app/logs

# Set environment variables
ENV PYTHONPATH="/app/backend:$PYTHONPATH"
ENV PORT=8000

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Start command
CMD ["python", "backend/server.py"]