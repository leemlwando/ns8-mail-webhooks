FROM python:3.9-slim

LABEL maintainer="Lee M. Lwando <leemlwando@gmail.com>"
LABEL org.opencontainers.image.source="https://github.com/leemlwando/ns8-mail-webhooks"
LABEL org.opencontainers.image.description="NethServer 8 Mail Webhooks Module"
LABEL org.opencontainers.image.author="Lee M. Lwando"

# Add NethServer 8 specific labels
LABEL org.nethserver.authorizations="traefik@node:routeadm"
LABEL org.nethserver.tcp-ports-demand="1"
LABEL org.nethserver.rootfull="0"
LABEL org.nethserver.images="ghcr.io/leemlwando/ns8-mail-webhooks:latest"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy application files
COPY imageroot /imageroot
COPY ui/dist /ui

# Make entrypoint executable
RUN chmod +x /imageroot/bin/entrypoint

# Set working directory
WORKDIR /imageroot

EXPOSE 8000

ENTRYPOINT ["/imageroot/bin/entrypoint"]
