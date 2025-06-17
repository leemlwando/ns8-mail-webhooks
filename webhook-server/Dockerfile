# Dockerfile for NS8 Mail Webhooks Server
# 
# Copyright (C) 2025 Lee M. Lwando <leemlwando@gmail.com>
# Licensed under GPL-3.0

FROM denoland/deno:1.40.0

LABEL maintainer="Lee M. Lwando <leemlwando@gmail.com>"
LABEL description="High-performance webhook server for NS8 Mail Webhooks module"
LABEL version="1.0.0"

# Set working directory
WORKDIR /app

# Create data directory with proper permissions
RUN mkdir -p /app/data && \
    chown -R deno:deno /app/data

# Copy configuration files
COPY deno.json ./
COPY deno.lock* ./

# Cache dependencies
RUN deno cache --lock=deno.lock deno.json || deno cache deno.json

# Copy source code
COPY . .

# Set proper ownership
RUN chown -R deno:deno /app

# Switch to non-root user
USER deno

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD deno run --allow-net --allow-env healthcheck.ts

# Set environment variables
ENV DENO_ENV=production
ENV API_PORT=3000
ENV DATA_DIR=/app/data

# Start the server
CMD ["deno", "run", "--allow-net", "--allow-read", "--allow-write", "--allow-env", "main.ts"]
