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
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Create directories
RUN mkdir -p /var/lib/nethserver/mail-webhooks /imageroot /ui

# Copy requirements and install Python dependencies
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy application files
COPY imageroot /imageroot
COPY ui/dist /ui

# Make scripts executable
RUN chmod +x /imageroot/bin/entrypoint && \
    find /imageroot/actions -name "*.py" -exec chmod +x {} \; && \
    find /imageroot/actions -name "*[0-9]*" -exec chmod +x {} \;

# Set proper permissions
RUN chown -R 1000:1000 /imageroot /ui /var/lib/nethserver/mail-webhooks

# Set working directory
WORKDIR /imageroot

# Create a non-root user
RUN useradd -u 1000 -m -s /bin/bash module-user
USER module-user

EXPOSE 8000

ENTRYPOINT ["/imageroot/bin/entrypoint"]
