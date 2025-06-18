#!/bin/bash

#
# Server-side fix script for ns8-mail-webhooks module
# This script should be run on the Rocky Linux server as the module user
#

set -e

echo "=== NS8 Mail Webhooks - Server Permission Fix ==="
echo "This script will fix permissions and rebuild the backend image"
echo

# Get the module instance path (assuming this script is run from the module directory)
MODULE_ROOT=$(pwd)
echo "Module root: ${MODULE_ROOT}"

# Determine the module user (usually mail-webhooks1, mail-webhooks2, etc.)
MODULE_USER=$(whoami)
echo "Module user: ${MODULE_USER}"

echo
echo "=== Step 1: Fixing script permissions ==="

# Fix permissions on all action scripts
find "${MODULE_ROOT}/actions" -name "[0-9]*" -type f | while read script; do
    echo "Setting executable permission on: ${script}"
    chmod +x "${script}"
done

# Fix permissions on bin scripts
find "${MODULE_ROOT}/bin" -type f | while read script; do
    echo "Setting executable permission on: ${script}"
    chmod +x "${script}"
done

# Fix permissions on any other scripts
find "${MODULE_ROOT}" -name "*.sh" -type f | while read script; do
    echo "Setting executable permission on: ${script}"
    chmod +x "${script}"
done

echo
echo "=== Step 2: Checking line endings ==="

# Convert any Windows line endings to Unix
find "${MODULE_ROOT}" -type f \( -name "*.service" -o -name "*.sh" -o -name "[0-9]*" \) | while read file; do
    if file "${file}" | grep -q "CRLF"; then
        echo "Converting line endings for: ${file}"
        sed -i 's/\r$//' "${file}"
    fi
done

echo
echo "=== Step 3: Stopping services ==="

# Stop the services if they're running
systemctl --user stop mail-webhooks.service 2>/dev/null || echo "mail-webhooks.service was not running"
systemctl --user stop mail-monitor.service 2>/dev/null || echo "mail-monitor.service was not running"

echo
echo "=== Step 4: Cleaning up old images ==="

# Remove any existing backend images to ensure a clean build
BACKEND_IMAGE="localhost/mail-webhooks-backend:latest"
if podman image exists "${BACKEND_IMAGE}"; then
    echo "Removing existing backend image: ${BACKEND_IMAGE}"
    podman rmi "${BACKEND_IMAGE}" || true
fi

# Remove any dangling images
echo "Cleaning up dangling images..."
podman image prune -f || true

echo
echo "=== Step 5: Building backend image ==="

# Change to the API directory and build the image
cd "${MODULE_ROOT}/api"
echo "Building backend image: ${BACKEND_IMAGE}"

if podman build -t "${BACKEND_IMAGE}" .; then
    echo "✓ Successfully built backend image: ${BACKEND_IMAGE}"
else
    echo "✗ Failed to build backend image"
    exit 1
fi

# Verify the image
if podman image exists "${BACKEND_IMAGE}"; then
    echo "✓ Backend image verified: ${BACKEND_IMAGE}"
    IMAGE_ID=$(podman image inspect "${BACKEND_IMAGE}" --format "{{.Id}}" | head -c 12)
    echo "  Image ID: ${IMAGE_ID}"
else
    echo "✗ Backend image verification failed"
    exit 1
fi

echo
echo "=== Step 6: Setting environment variables ==="

cd "${MODULE_ROOT}"

# Ensure the environment file exists and has the correct backend image setting
ENV_FILE="${MODULE_ROOT}/environment"
if [ -f "${ENV_FILE}" ]; then
    # Update existing environment file
    if grep -q "MAIL_WEBHOOKS_BACKEND_IMAGE" "${ENV_FILE}"; then
        sed -i "s|MAIL_WEBHOOKS_BACKEND_IMAGE=.*|MAIL_WEBHOOKS_BACKEND_IMAGE=${BACKEND_IMAGE}|" "${ENV_FILE}"
    else
        echo "MAIL_WEBHOOKS_BACKEND_IMAGE=${BACKEND_IMAGE}" >> "${ENV_FILE}"
    fi
else
    # Create new environment file
    echo "MAIL_WEBHOOKS_BACKEND_IMAGE=${BACKEND_IMAGE}" > "${ENV_FILE}"
fi

echo "✓ Environment variable set: MAIL_WEBHOOKS_BACKEND_IMAGE=${BACKEND_IMAGE}"

echo
echo "=== Step 7: Reloading systemd and starting services ==="

# Reload systemd user daemon
systemctl --user daemon-reload

# Start the services
echo "Starting mail-webhooks.service..."
if systemctl --user start mail-webhooks.service; then
    echo "✓ mail-webhooks.service started successfully"
else
    echo "✗ Failed to start mail-webhooks.service"
    echo "Checking service status..."
    systemctl --user status mail-webhooks.service --no-pager || true
    echo "Checking service logs..."
    journalctl --user -u mail-webhooks.service -n 20 --no-pager || true
    exit 1
fi

echo
echo "=== Step 8: Verifying service status ==="

# Check service status
echo "Service status:"
systemctl --user status mail-webhooks.service --no-pager

echo
echo "Recent service logs:"
journalctl --user -u mail-webhooks.service -n 10 --no-pager

echo
echo "=== Step 9: Testing configuration action ==="

# Test the get-configuration action
echo "Testing get-configuration action..."
if "${MODULE_ROOT}/actions/get-configuration/20read"; then
    echo "✓ get-configuration action executed successfully"
else
    echo "✗ get-configuration action failed"
    exit 1
fi

echo
echo "=== Fix completed successfully! ==="
echo
echo "The ns8-mail-webhooks module should now be working correctly."
echo "You can check the service status with:"
echo "  systemctl --user status mail-webhooks.service"
echo
echo "Check the API is responding with:"
echo "  curl -s http://127.0.0.1:20080/api/health"
echo
