#!/bin/bash

echo "Testing Mail Webhooks service startup..."

# Set some default environment variables for testing
export TCP_PORT="8080"
export MONGODB_URL="mongodb://localhost:27017"
export MAIL_SERVER_UUID="test-uuid"
export WEBHOOKS_COLLECTION="webhooks"
export EVENTS_COLLECTION="events"
export SETTINGS_COLLECTION="settings"
export TRIGGERS_COLLECTION="triggers"
export LOGS_COLLECTION="logs"

echo "Testing podman run command..."

podman run --rm \
    --publish=127.0.0.1:${TCP_PORT}:8080 \
    --volume=./imageroot/api:/app:Z \
    --env=MONGODB_URL=${MONGODB_URL} \
    --env=MAIL_SERVER_UUID=${MAIL_SERVER_UUID} \
    --env=WEBHOOKS_COLLECTION=${WEBHOOKS_COLLECTION} \
    --env=EVENTS_COLLECTION=${EVENTS_COLLECTION} \
    --env=SETTINGS_COLLECTION=${SETTINGS_COLLECTION} \
    --env=TRIGGERS_COLLECTION=${TRIGGERS_COLLECTION} \
    --env=LOGS_COLLECTION=${LOGS_COLLECTION} \
    --workdir=/app \
    python:3.11-slim bash -c "cd /app && pip install --no-cache-dir -r requirements.txt && python -m uvicorn app:app --host 0.0.0.0 --port 8080"
