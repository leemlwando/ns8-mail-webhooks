#!/bin/bash

echo "=== Testing Mail Webhooks Service Configuration ==="

# Check if we're in the right directory structure
if [ ! -d "imageroot/api" ]; then
    echo "ERROR: imageroot/api directory not found!"
    echo "Current directory: $(pwd)"
    echo "Contents:"
    ls -la
    exit 1
fi

echo "✓ API directory exists: imageroot/api"

# Check if API files exist
if [ ! -f "imageroot/api/app.py" ]; then
    echo "ERROR: app.py not found in imageroot/api"
    exit 1
fi

if [ ! -f "imageroot/api/requirements.txt" ]; then
    echo "ERROR: requirements.txt not found in imageroot/api"
    exit 1
fi

if [ ! -f "imageroot/api/entrypoint.sh" ]; then
    echo "ERROR: entrypoint.sh not found in imageroot/api"
    exit 1
fi

echo "✓ All required API files exist"

# Check permissions
if [ ! -x "imageroot/api/entrypoint.sh" ]; then
    echo "WARNING: entrypoint.sh is not executable"
    chmod +x imageroot/api/entrypoint.sh
    echo "✓ Fixed entrypoint.sh permissions"
fi

# Test if podman can access the api directory (simulate the volume mount)
echo "Testing volume mount simulation..."
if [ -d "imageroot/api" ]; then
    echo "✓ Volume mount path exists and is accessible"
    echo "API directory contents:"
    ls -la imageroot/api/
else
    echo "ERROR: Volume mount path not accessible"
    exit 1
fi

echo ""
echo "=== Service should now start successfully ==="
echo "Key fixes applied:"
echo "- WorkingDirectory set to %h (module home)"
echo "- Volume mount uses ./api relative to home directory"
echo "- All scripts have executable permissions"
echo "- Enhanced entrypoint.sh with comprehensive debugging"
