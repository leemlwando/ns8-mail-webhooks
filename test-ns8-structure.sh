#!/bin/bash

echo "=== NS8 Module Directory Structure Test ==="
echo ""
echo "This script simulates the NS8 module installation process"
echo ""

# Simulate the NS8 installation process
echo "1. Creating test module home directory:"
TEST_HOME="/tmp/test-ns8-mail-webhooks8"
rm -rf "$TEST_HOME"
mkdir -p "$TEST_HOME"
cd "$TEST_HOME"

echo "   Created: $TEST_HOME"

echo ""
echo "2. Simulating imageroot extraction (what NS8 does during module installation):"
echo "   Copying imageroot contents to module home..."

# This simulates what happens during NS8 module installation
# The imageroot contents are extracted directly to the module home
cp -r "${PWD%/*}/imageroot/"* "$TEST_HOME/"

echo ""
echo "3. Checking directory structure after installation:"
echo "   Contents of module home directory:"
find "$TEST_HOME" -maxdepth 2 -type d | sort

echo ""
echo "4. Checking if api directory exists:"
if [ -d "$TEST_HOME/api" ]; then
    echo "   ✓ api directory found at: $TEST_HOME/api"
    echo "   Contents:"
    ls -la "$TEST_HOME/api/"
else
    echo "   ✗ api directory NOT found"
    echo "   Available directories:"
    ls -la "$TEST_HOME/"
fi

echo ""
echo "5. Testing volume mount path:"
cd "$TEST_HOME"
if [ -d "./api" ]; then
    echo "   ✓ ./api resolves correctly from module home"
    echo "   This confirms the systemd service volume mount './api:/app:Z' should work"
else
    echo "   ✗ ./api does NOT resolve from module home"
    echo "   The systemd service volume mount needs to be fixed"
fi

echo ""
echo "Cleanup:"
rm -rf "$TEST_HOME"
