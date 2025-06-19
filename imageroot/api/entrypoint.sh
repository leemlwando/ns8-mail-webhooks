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

# Check environment variables but don't fail if MongoDB URL is missing
# (it might be provided via environment files by systemd)
if [ -z "$MONGODB_URL" ]; then
    echo "NOTE: MONGODB_URL environment variable is not set in startup environment"
    echo "Will check for it during MongoDB connection test..."
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
import sys

try:
    mongodb_url = os.environ.get('MONGODB_URL')
    if not mongodb_url:
        print('WARNING: MONGODB_URL environment variable is not set!')
        print('Will attempt to start without MongoDB connection')
    else:
        print(f'Testing connection to: {mongodb_url[:30]}...')
        client = MongoClient(mongodb_url, serverSelectionTimeoutMS=5000)
        client.server_info()
        print('MongoDB connection successful')
        client.close()
except Exception as e:
    print(f'MongoDB connection failed: {e}')
    print('WARNING: Starting without MongoDB connection')
    # Don't exit - let the app start and handle the connection issue
"

echo ""
echo "=== Starting FastAPI Application ==="
echo "Starting uvicorn server on 0.0.0.0:8080..."

# Try main.py first, then app.py as fallback
if [ -f "main.py" ]; then
    echo "Using main.py as entry point"
    exec python3 main.py
else
    echo "Using app.py as entry point"
    exec python3 -m uvicorn app:app --host 0.0.0.0 --port 8080 --log-level info
fi
