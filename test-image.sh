#!/bin/bash

#
# Test script to verify the NS8 Mail Webhooks image works correctly
#

set -e

echo "🧪 Testing NS8 Mail Webhooks image..."

# Build the image
echo "🏗️ Building the image..."
./build-docker.sh

# Test the image can start
echo "🚀 Testing image startup..."
CONTAINER_ID=$(docker run -d -p 8001:8000 \
    -e DATABASE_URL="sqlite:////tmp/test.db" \
    -e IMAP_HOST="localhost" \
    -e IMAP_PORT="993" \
    ghcr.io/leemlwando/ns8-mail-webhooks:latest)

echo "📋 Container ID: $CONTAINER_ID"

# Wait for startup
echo "⏳ Waiting for service to start..."
sleep 10

# Test the status endpoint
echo "🔍 Testing API endpoints..."
if curl -f http://localhost:8001/api/status; then
    echo "✅ Status endpoint working"
else
    echo "❌ Status endpoint failed"
    docker logs $CONTAINER_ID
    docker stop $CONTAINER_ID
    docker rm $CONTAINER_ID
    exit 1
fi

# Test the schedules endpoint
if curl -f http://localhost:8001/api/schedules/; then
    echo "✅ Schedules endpoint working"
else
    echo "❌ Schedules endpoint failed"
    docker logs $CONTAINER_ID
    docker stop $CONTAINER_ID
    docker rm $CONTAINER_ID
    exit 1
fi

# Check logs for any errors
echo "📋 Container logs:"
docker logs $CONTAINER_ID

# Cleanup
echo "🧹 Cleaning up..."
docker stop $CONTAINER_ID
docker rm $CONTAINER_ID

echo "✅ Image test completed successfully!"
echo ""
echo "🚀 Image is ready for NethServer 8 deployment"
echo "💡 To install: add-module ghcr.io/leemlwando/ns8-mail-webhooks:latest 1"
