#!/bin/bash
set -e

echo "Starting Mail Webhooks API..."
echo "Python version: $(python --version)"
echo "Working directory: $(pwd)"
echo "Files in current directory:"
ls -la

echo "Installing dependencies..."
if [ ! -f "requirements.txt" ]; then
    echo "ERROR: requirements.txt not found!"
    exit 1
fi

pip install --no-cache-dir -r requirements.txt

echo "Dependencies installed successfully"
echo "Environment variables:"
echo "  MONGODB_URL: ${MONGODB_URL:0:20}..."
echo "  MAIL_SERVER_UUID: ${MAIL_SERVER_UUID}"
echo "  WEBHOOKS_COLLECTION: ${WEBHOOKS_COLLECTION:-webhooks}"
echo "  EVENTS_COLLECTION: ${EVENTS_COLLECTION:-events}"
echo "  SETTINGS_COLLECTION: ${SETTINGS_COLLECTION:-settings}"
echo "  TRIGGERS_COLLECTION: ${TRIGGERS_COLLECTION:-triggers}"
echo "  LOGS_COLLECTION: ${LOGS_COLLECTION:-logs}"

echo "Checking if app.py exists..."
if [ ! -f "app.py" ]; then
    echo "ERROR: app.py not found!"
    exit 1
fi

echo "Starting FastAPI application with mail monitor service..."
exec python main.py
