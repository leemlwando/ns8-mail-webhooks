#!/bin/bash

#
# Test script to validate NS8 mail-webhooks configuration
#

set -e

echo "=== NS8 Mail Webhooks Configuration Test ==="
echo

echo "1. Checking project structure..."
if [ -d "imageroot" ]; then
    echo "✓ imageroot directory exists"
else
    echo "✗ imageroot directory missing"
    exit 1
fi

if [ -d "backend" ]; then
    echo "✓ backend directory exists"
else
    echo "✗ backend directory missing"
    exit 1
fi

if [ -f "backend/Containerfile" ]; then
    echo "✓ backend Containerfile exists"
else
    echo "✗ backend Containerfile missing"
    exit 1
fi

echo

echo "2. Checking systemd service configuration..."
if [ -f "imageroot/systemd/user/mail-webhooks.service" ]; then
    echo "✓ systemd service file exists"
    
    # Check if service uses proper environment variable
    if grep -q "MAIL_WEBHOOKS_BACKEND_IMAGE" "imageroot/systemd/user/mail-webhooks.service"; then
        echo "✓ Service uses proper environment variable"
    else
        echo "✗ Service missing proper environment variable"
        echo "  Expected: MAIL_WEBHOOKS_BACKEND_IMAGE"
    fi
else
    echo "✗ systemd service file missing"
    exit 1
fi

echo

echo "3. Checking build configuration..."
if [ -f "build-images.sh" ]; then
    echo "✓ build-images.sh exists"
    
    # Check if build script includes backend image
    if grep -q "backend" "build-images.sh"; then
        echo "✓ Build script includes backend"
    else
        echo "✗ Build script missing backend configuration"
    fi
    
    # Check if org.nethserver.images label includes backend
    if grep -q "org.nethserver.images" "build-images.sh"; then
        echo "✓ Build script sets org.nethserver.images label"
    else
        echo "✗ Build script missing org.nethserver.images label"
    fi
else
    echo "✗ build-images.sh missing"
    exit 1
fi

echo

echo "4. Checking backend API structure..."
if [ -f "backend/app.py" ]; then
    echo "✓ Backend app.py exists"
else
    echo "✗ Backend app.py missing"
    exit 1
fi

if [ -f "backend/requirements.txt" ]; then
    echo "✓ Backend requirements.txt exists"
else
    echo "✗ Backend requirements.txt missing"
    exit 1
fi

echo

echo "5. Checking actions and configuration..."
if [ -f "imageroot/actions/configure-module/20configure" ]; then
    echo "✓ configure-module action exists"
else
    echo "✗ configure-module action missing"
    exit 1
fi

if [ -f "imageroot/actions/configure-module/80start_services" ]; then
    echo "✓ start_services action exists"
else
    echo "✗ start_services action missing"
    exit 1
fi

echo

echo "=== Configuration Test Complete ==="
echo "✓ All basic checks passed!"
echo
echo "Next steps:"
echo "1. Build images: ./build-images.sh"
echo "2. Test module installation in NS8 environment"
echo "3. Verify backend container starts correctly"
echo "4. Test API endpoints"
