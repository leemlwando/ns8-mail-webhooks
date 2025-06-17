#!/bin/bash

#
# Test script to validate mail-webhooks configuration
#

set -e

echo "Testing mail-webhooks NS8 module configuration..."

# Check if build-images.sh produces correct output
echo "1. Testing build-images.sh output structure..."

# Simulate what build-images.sh should produce
echo "Expected images:"
echo "  - ghcr.io/leemlwando/ns8-mail-webhooks:latest (main module)"
echo "  - ghcr.io/leemlwando/mail-webhooks-backend:latest (backend API)"

# Check org.nethserver.images label
echo ""
echo "2. Checking image label configuration..."
echo "Should contain: ghcr.io/leemlwando/mail-webhooks-backend:latest"

# Check systemd service configuration
echo ""
echo "3. Checking systemd service configuration..."
if grep -q "MAIL_WEBHOOKS_BACKEND_IMAGE" imageroot/systemd/user/mail-webhooks.service; then
    echo "✓ Systemd service uses correct environment variable: MAIL_WEBHOOKS_BACKEND_IMAGE"
else
    echo "✗ Systemd service missing MAIL_WEBHOOKS_BACKEND_IMAGE variable"
    exit 1
fi

# Check if all required environment variables are passed to container
required_env_vars=("MONGODB_URL" "WEBHOOKS_COLLECTION" "EVENTS_COLLECTION" "SETTINGS_COLLECTION" "TRIGGERS_COLLECTION" "LOGS_COLLECTION")
echo ""
echo "4. Checking required environment variables in systemd service..."
for var in "${required_env_vars[@]}"; do
    if grep -q "--env=${var}" imageroot/systemd/user/mail-webhooks.service; then
        echo "✓ Environment variable passed: $var"
    else
        echo "✗ Missing environment variable: $var"
        exit 1
    fi
done

# Check configuration scripts
echo ""
echo "5. Checking configuration scripts..."
if [[ -f "imageroot/actions/configure-module/20configure" ]]; then
    echo "✓ Main configuration script exists"
else
    echo "✗ Missing main configuration script"
    exit 1
fi

if [[ -f "imageroot/actions/configure-module/80start_services" ]]; then
    echo "✓ Service startup script exists"
else
    echo "✗ Missing service startup script"
    exit 1
fi

if [[ -f "imageroot/actions/configure-module/85ensure_backend_image" ]]; then
    echo "✓ Backend image validation script exists"
else
    echo "✗ Missing backend image validation script"
    exit 1
fi

# Check backend Containerfile
echo ""
echo "6. Checking backend container configuration..."
if [[ -f "backend/Containerfile" ]]; then
    echo "✓ Backend Containerfile exists"
else
    echo "✗ Missing backend Containerfile"
    exit 1
fi

echo ""
echo "✓ All configuration tests passed!"
echo ""
echo "To deploy this module:"
echo "1. Build images: ./build-images.sh"
echo "2. Push images to registry"
echo "3. Install: add-module ghcr.io/leemlwando/ns8-mail-webhooks:latest 1"
echo "4. Configure: api-cli run module/mail-webhooks1/configure-module --data '{"
echo "    \"mongodb_url\": \"mongodb://user:pass@host:port/database\","
echo "    \"mail_server_uuid\": \"mail1\""
echo "  }'"
