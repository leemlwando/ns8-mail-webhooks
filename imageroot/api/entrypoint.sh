#!/bin/bash
set -e

echo "=== Mail Webhooks API Container Startup ==="
echo "Timestamp: $(date)"
echo "Working directory: $(pwd)"
echo "User: $(whoami)"

echo ""
echo "=== Environment Check ==="
echo "Python version: $(python3 --version)"
echo "Pip version: $(pip --version)"

echo ""
echo "=== File System Check ==="
echo "Current directory contents:"
ls -la

if [ ! -f "requirements.txt" ]; then
    echo "ERROR: requirements.txt not found!"
    echo "Expected to find it in $(pwd)"
    exit 1
fi

if [ ! -f "app.py" ]; then
    echo "ERROR: app.py not found!"
    echo "Expected to find it in $(pwd)" 
    exit 1
fi

echo ""
echo "=== Environment Variables ==="
echo "MONGODB_URL: ${MONGODB_URL:0:30}..."
echo "MAIL_SERVER_UUID: ${MAIL_SERVER_UUID}"
echo "WEBHOOKS_COLLECTION: ${WEBHOOKS_COLLECTION:-webhooks}"
echo "EVENTS_COLLECTION: ${EVENTS_COLLECTION:-events}"
echo "SETTINGS_COLLECTION: ${SETTINGS_COLLECTION:-settings}"
echo "TRIGGERS_COLLECTION: ${TRIGGERS_COLLECTION:-triggers}"
echo "LOGS_COLLECTION: ${LOGS_COLLECTION:-logs}"

# Validate required environment variables
if [ -z "$MONGODB_URL" ]; then
    echo "ERROR: MONGODB_URL environment variable is not set!"
    exit 1
fi

echo ""
echo "=== Installing Dependencies ==="
pip install --no-cache-dir -r requirements.txt

echo ""
echo "=== Testing Imports ==="
python3 -c "import fastapi, uvicorn, pymongo, requests, pydantic; print('All imports successful')"

echo ""
echo "=== Testing MongoDB Connection ==="
python3 -c "
from pymongo import MongoClient
import os
client = MongoClient(os.environ['MONGODB_URL'], serverSelectionTimeoutMS=5000)
try:
    client.server_info()
    print('MongoDB connection successful')
except Exception as e:
    print(f'MongoDB connection failed: {e}')
    exit(1)
"

echo ""
echo "=== Starting FastAPI Application ==="
echo "Starting uvicorn server on 0.0.0.0:8080..."
exec python3 -m uvicorn app:app --host 0.0.0.0 --port 8080 --log-level info
