# Dockerfile for NS8 Mail Webhooks Module
# 
# Copyright (C) 2025 Lee M. Lwando <leemlwando@gmail.com>
# Licensed under GPL-3.0

FROM python:3.11-slim

LABEL maintainer="Lee M. Lwando <leemlwando@gmail.com>"
LABEL description="NS8 Mail Webhooks Module - Python Backend"
LABEL version="1.0.0"

# Install system dependencies required for NS8 agent and module functionality
RUN apt-get update && apt-get install -y \
    curl \
    sqlite3 \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    requests \
    aiohttp \
    pydantic

# Create application directories following NS8 patterns
WORKDIR /

# Copy module files following NS8 structure
COPY actions/ /imageroot/actions/
COPY bin/ /imageroot/bin/
COPY pypkg/ /imageroot/pypkg/
COPY systemd/ /imageroot/systemd/
COPY events/ /imageroot/events/

# Set executable permissions for NS8 actions and scripts
RUN find /imageroot/actions/ -name "*" -type f -exec chmod +x {} \; && \
    find /imageroot/bin/ -name "*" -type f -exec chmod +x {} \; && \
    find /imageroot/events/ -name "*" -type f -exec chmod +x {} \; 2>/dev/null || true

# Create data directories for module state
RUN mkdir -p /var/lib/nethserver/mail-webhooks/data && \
    mkdir -p /var/lib/nethserver/mail-webhooks/logs

# Health check for NS8 monitoring
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python3 -c "import os; exit(0 if os.path.exists('/imageroot/pypkg/config_manager.py') else 1)"

# Default entrypoint for NS8 containers
ENTRYPOINT ["/imageroot/bin/module-events"]
