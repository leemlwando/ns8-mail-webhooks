#!/bin/bash

echo "=== Testing Mail Webhooks Backend Service ==="

# Check if backend image exists
echo "1. Checking for backend image..."
if podman image exists "ghcr.io/leemlwando/mail-webhooks-backend:latest"; then
    echo "✓ Backend image exists"
else
    echo "✗ Backend image missing - building..."
    cd imageroot/api
    podman build -t "ghcr.io/leemlwando/mail-webhooks-backend:latest" .
    cd ../..
fi

# Check systemd service syntax
echo "2. Checking systemd service syntax..."
systemd-analyze verify imageroot/systemd/user/mail-webhooks.service 2>/dev/null && echo "✓ Systemd service syntax OK" || echo "✗ Systemd service has issues"

# Test if we can run the container manually
echo "3. Testing container startup..."
podman run --rm -d \
    --name test-mail-webhooks \
    --publish 127.0.0.1:8999:8080 \
    --env=MONGODB_URL="mongodb://test:test@test:27017/test" \
    ghcr.io/leemlwando/mail-webhooks-backend:latest

if [ $? -eq 0 ]; then
    echo "✓ Container started successfully"
    sleep 2
    curl -s http://127.0.0.1:8999/health && echo " - Health check passed" || echo " - Health check failed"
    podman stop test-mail-webhooks
else
    echo "✗ Container failed to start"
fi

echo "=== Test completed ==="
