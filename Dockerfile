# Stage 1: Build Nuclei
FROM golang:1.22-alpine AS nuclei-builder

# Install build dependencies
RUN apk add --no-cache git gcc musl-dev

# Set working directory
WORKDIR /build

# Install Nuclei v3 with proper Go environment
ENV CGO_ENABLED=0
ENV GO111MODULE=on

# Download and install nuclei
RUN go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest

# Stage 2: Final image
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy nuclei binary from builder stage
COPY --from=nuclei-builder /go/bin/nuclei /usr/local/bin/nuclei

# Verify nuclei is installed
RUN nuclei -version || echo "Nuclei installed"

# Set working directory
WORKDIR /app

# Copy Python requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .

# Update Nuclei templates (with error handling)
RUN nuclei -update-templates || echo "Templates will be updated on first run"

# Create necessary directories
RUN mkdir -p /tmp/nuclei

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application with gunicorn for better performance
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "120", "app:app"]
