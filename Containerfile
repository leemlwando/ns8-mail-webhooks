FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd --system --create-home --shell /bin/bash mailwebhook

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY imageroot/pypkg/ /app/

# Create data directory with proper permissions
RUN mkdir -p /var/lib/nethserver/mail-webhook && \
    chown -R mailwebhook:mailwebhook /var/lib/nethserver/mail-webhook /app

USER mailwebhook

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/api/health', timeout=5)"

EXPOSE 8080

CMD ["python", "-m", "mailwebhook.main"]
