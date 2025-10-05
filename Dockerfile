FROM golang:1.21-alpine AS nuclei-builder
RUN apk add --no-cache git
RUN go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest

FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=nuclei-builder /go/bin/nuclei /usr/local/bin/nuclei
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
RUN nuclei -update-templates
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"
CMD ["python", "app.py"]
